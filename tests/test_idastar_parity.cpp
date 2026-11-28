#include "src/PompeiuHausdorff.h"
#include "src/DistanceSearchEngine.h"

#include <Eigen/Core>
#include <igl/readOBJ.h>

#include <cmath>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using RowMatrixXd = Eigen::Matrix<double, Eigen::Dynamic, 3, Eigen::RowMajor>;
using RowMatrixXi = Eigen::Matrix<int, Eigen::Dynamic, 3, Eigen::RowMajor>;

void require(bool condition, const std::string& message)
{
    if (!condition) {
        throw std::runtime_error("Assertion failed: " + message);
    }
}

void make_unit_cube(RowMatrixXd& V, RowMatrixXi& F)
{
    V.resize(8, 3);
    V << 0.0, 0.0, 0.0,
         1.0, 0.0, 0.0,
         1.0, 1.0, 0.0,
         0.0, 1.0, 0.0,
         0.0, 0.0, 1.0,
         1.0, 0.0, 1.0,
         1.0, 1.0, 1.0,
         0.0, 1.0, 1.0;

    F.resize(12, 3);
    F << 0, 2, 1,
         0, 3, 2,
         4, 5, 6,
         4, 6, 7,
         0, 1, 5,
         0, 5, 4,
         1, 2, 6,
         1, 6, 5,
         2, 3, 7,
         2, 7, 6,
         3, 0, 4,
         3, 4, 7;
}

void make_icosahedron(RowMatrixXd& V, RowMatrixXi& F)
{
    const double phi = (1.0 + std::sqrt(5.0)) / 2.0;
    V.resize(12, 3);
    V << -1.0,  phi,  0.0,
          1.0,  phi,  0.0,
         -1.0, -phi,  0.0,
          1.0, -phi,  0.0,
          0.0, -1.0,  phi,
          0.0,  1.0,  phi,
          0.0, -1.0, -phi,
          0.0,  1.0, -phi,
          phi,  0.0, -1.0,
          phi,  0.0,  1.0,
         -phi,  0.0, -1.0,
         -phi,  0.0,  1.0;
    V.rowwise().normalize();

    F.resize(20, 3);
    F << 0, 11, 5,
         0,  5, 1,
         0,  1, 7,
         0,  7, 10,
         0, 10, 11,
         1,  5, 9,
         5, 11, 4,
         11, 10, 2,
         10, 7, 6,
         7,  1, 8,
         3,  9, 4,
         3,  4, 2,
         3,  2, 6,
         3,  6, 8,
         3,  8, 9,
         4,  9, 5,
         2,  4, 11,
         6,  2, 10,
         8,  6, 7,
         9,  8, 1;
}

void subdivide_sphere_once(const RowMatrixXd& V_in, const RowMatrixXi& F_in, RowMatrixXd& V_out, RowMatrixXi& F_out)
{
    std::vector<Eigen::RowVector3d> verts(V_in.rows());
    for (int i = 0; i < V_in.rows(); ++i) {
        verts[i] = V_in.row(i);
    }

    std::vector<Eigen::RowVector3i> faces;
    faces.reserve(F_in.rows() * 4);

    for (int f = 0; f < F_in.rows(); ++f) {
        const int i0 = F_in(f, 0);
        const int i1 = F_in(f, 1);
        const int i2 = F_in(f, 2);

        const int m01 = static_cast<int>(verts.size());
        verts.push_back((0.5 * (V_in.row(i0) + V_in.row(i1))).normalized());
        const int m12 = static_cast<int>(verts.size());
        verts.push_back((0.5 * (V_in.row(i1) + V_in.row(i2))).normalized());
        const int m20 = static_cast<int>(verts.size());
        verts.push_back((0.5 * (V_in.row(i2) + V_in.row(i0))).normalized());

        faces.emplace_back(i0, m01, m20);
        faces.emplace_back(i1, m12, m01);
        faces.emplace_back(i2, m20, m12);
        faces.emplace_back(m01, m12, m20);
    }

    V_out.resize(static_cast<int>(verts.size()), 3);
    for (int i = 0; i < V_out.rows(); ++i) {
        V_out.row(i) = verts[i];
    }
    F_out.resize(static_cast<int>(faces.size()), 3);
    for (int i = 0; i < F_out.rows(); ++i) {
        F_out.row(i) = faces[i];
    }
}

void assert_engine_parity(
    const std::string& label,
    const RowMatrixXd& VA,
    const RowMatrixXi& FA,
    const RowMatrixXd& VB,
    const RowMatrixXi& FB,
    double tol,
    bool normalize,
    const phd::search::IDAStarConfig& cfg)
{
    const double max_factor = 1000000.0;
    PompeiuHausdorff bf(
        VA, FA, VB, FB, tol, max_factor, normalize,
        phd::search::SearchEngineType::BestFirst);
    PompeiuHausdorff ida(
        VA, FA, VB, FB, tol, max_factor, normalize,
        phd::search::SearchEngineType::IDAStar, cfg);

    const double tol_scaled = tol * ida.dA;
    const double eps_slack = tol_scaled * 1e-6 + 1e-12;

    require(std::abs(bf.dA - ida.dA) <= 1e-12, label + ": dA mismatch");
    require(ida.lower <= ida.upper_max + 1e-12, label + ": inverted IDA* interval");
    require(
        (ida.upper_max - ida.lower) <= tol_scaled + eps_slack,
        label + ": IDA* failed to meet tolerance");

    const bool intervals_overlap =
        !(bf.upper_max + eps_slack < ida.lower || ida.upper_max + eps_slack < bf.lower);
    require(intervals_overlap, label + ": intervals [l, u] do not overlap between BF and IDA*");
}

void test_identical_mesh()
{
    RowMatrixXd V;
    RowMatrixXi F;
    make_unit_cube(V, F);

    for (auto policy : {
             phd::search::ThresholdPolicy::NextBest,
             phd::search::ThresholdPolicy::FixedDecay,
             phd::search::ThresholdPolicy::AdaptiveHistogram}) {
        phd::search::IDAStarConfig cfg;
        cfg.threshold_policy = policy;
        assert_engine_parity("identical_cube", V, F, V, F, 1e-5, true, cfg);
    }
    std::cout << "[PASS] test_identical_mesh\n";
}

void test_translated_cube_analytical()
{
    RowMatrixXd VA, VB;
    RowMatrixXi FA, FB;
    make_unit_cube(VA, FA);
    VB = VA;
    VB.col(0).array() += 0.05;
    FB = FA;

    for (bool normalize : {true, false}) {
        for (double tol : {1e-3, 1e-4, 1e-5}) {
            for (auto policy : {
                     phd::search::ThresholdPolicy::NextBest,
                     phd::search::ThresholdPolicy::FixedDecay,
                     phd::search::ThresholdPolicy::AdaptiveHistogram}) {
                phd::search::IDAStarConfig cfg;
                cfg.threshold_policy = policy;

                PompeiuHausdorff ida(
                    VA, FA, VB, FB, tol, 1000000.0, normalize,
                    phd::search::SearchEngineType::IDAStar, cfg);
                require(
                    ida.lower <= 0.05 + 1e-12 && 0.05 <= ida.upper_max + 1e-12,
                    "translated_cube: true distance 0.05 outside [lower, upper_max]");

                assert_engine_parity("translated_cube", VA, FA, VB, FB, tol, normalize, cfg);
            }
        }
    }
    std::cout << "[PASS] test_translated_cube_analytical\n";
}

void test_icosphere_refinement()
{
    RowMatrixXd V_coarse, V_fine;
    RowMatrixXi F_coarse, F_fine;
    make_icosahedron(V_coarse, F_coarse);
    subdivide_sphere_once(V_coarse, F_coarse, V_fine, F_fine);

    for (auto policy : {
             phd::search::ThresholdPolicy::NextBest,
             phd::search::ThresholdPolicy::FixedDecay,
             phd::search::ThresholdPolicy::AdaptiveHistogram,
             phd::search::ThresholdPolicy::Bisection}) {
        phd::search::IDAStarConfig cfg;
        cfg.threshold_policy = policy;
        assert_engine_parity("icosphere", V_fine, F_fine, V_coarse, F_coarse, 1e-4, true, cfg);
    }
    {
        phd::search::IDAStarConfig cfg_hybrid;
        cfg_hybrid.threshold_policy = phd::search::ThresholdPolicy::AdaptiveHistogram;
        cfg_hybrid.enable_warm_start = true;
        cfg_hybrid.warm_start_max_subdivisions = 64;
        assert_engine_parity("icosphere_hybrid", V_fine, F_fine, V_coarse, F_coarse, 1e-4, true, cfg_hybrid);
    }
    std::cout << "[PASS] test_icosphere_refinement\n";
}

void test_official_107100_parity_and_cache()
{
    Eigen::MatrixXd VA_dyn, VB_dyn;
    Eigen::MatrixXi FA_dyn, FB_dyn;
    const std::string mesh_a_path = std::string(TEST_MESHES_DIR) + "/107100.obj";
    const std::string mesh_b_path = std::string(TEST_MESHES_DIR) + "/107100_sf.obj";

    require(igl::readOBJ(mesh_a_path, VA_dyn, FA_dyn), "Failed to load 107100.obj");
    require(igl::readOBJ(mesh_b_path, VB_dyn, FB_dyn), "Failed to load 107100_sf.obj");

    RowMatrixXd VA = VA_dyn;
    RowMatrixXi FA = FA_dyn;
    RowMatrixXd VB = VB_dyn;
    RowMatrixXi FB = FB_dyn;

    for (double tol : {1e-2, 1e-3, 1e-4}) {
        phd::search::IDAStarConfig cfg_adaptive;
        cfg_adaptive.threshold_policy = phd::search::ThresholdPolicy::AdaptiveHistogram;
        cfg_adaptive.max_cache_depth = 4;
        assert_engine_parity("107100_adaptive_cached", VA, FA, VB, FB, tol, true, cfg_adaptive);

        phd::search::IDAStarConfig cfg_nocache = cfg_adaptive;
        cfg_nocache.max_cache_depth = 0;
        assert_engine_parity("107100_adaptive_nocache", VA, FA, VB, FB, tol, true, cfg_nocache);

        phd::search::IDAStarConfig cfg_fixed;
        cfg_fixed.threshold_policy = phd::search::ThresholdPolicy::FixedDecay;
        assert_engine_parity("107100_fixed", VA, FA, VB, FB, tol, true, cfg_fixed);

        phd::search::IDAStarConfig cfg_bisection;
        cfg_bisection.threshold_policy = phd::search::ThresholdPolicy::Bisection;
        assert_engine_parity("107100_bisection", VA, FA, VB, FB, tol, true, cfg_bisection);

        phd::search::IDAStarConfig cfg_hybrid;
        cfg_hybrid.threshold_policy = phd::search::ThresholdPolicy::AdaptiveHistogram;
        cfg_hybrid.enable_warm_start = true;
        cfg_hybrid.warm_start_max_subdivisions = 2000;
        assert_engine_parity("107100_hybrid", VA, FA, VB, FB, tol, true, cfg_hybrid);
    }

    // Verify NextBest policy on 107100 at tol=1e-2
    {
        phd::search::IDAStarConfig cfg_next_best;
        cfg_next_best.threshold_policy = phd::search::ThresholdPolicy::NextBest;
        assert_engine_parity("107100_next_best", VA, FA, VB, FB, 1e-2, true, cfg_next_best);
    }

    // Verify cached vs uncached exact consistency
    {
        phd::search::IDAStarConfig cfg_cached;
        cfg_cached.threshold_policy = phd::search::ThresholdPolicy::AdaptiveHistogram;
        cfg_cached.max_cache_depth = 4;

        phd::search::IDAStarConfig cfg_uncached = cfg_cached;
        cfg_uncached.max_cache_depth = 0;

        PompeiuHausdorff ida_cached(
            VA, FA, VB, FB, 1e-4, 1000000.0, true,
            phd::search::SearchEngineType::IDAStar, cfg_cached);
        PompeiuHausdorff ida_uncached(
            VA, FA, VB, FB, 1e-4, 1000000.0, true,
            phd::search::SearchEngineType::IDAStar, cfg_uncached);

        const double tol_scaled = 1e-4 * ida_cached.dA;
        require(
            std::abs(ida_cached.lower - ida_uncached.lower) <= tol_scaled + 1e-12,
            "Cached vs uncached lower bound divergence");
        require(
            std::abs(ida_cached.upper_max - ida_uncached.upper_max) <= tol_scaled + 1e-12,
            "Cached vs uncached upper bound divergence");
    }

    std::cout << "[PASS] test_official_107100_parity_and_cache\n";
}

void test_safety_limit_throws()
{
    RowMatrixXd VA, VB;
    RowMatrixXi FA, FB;
    make_unit_cube(VA, FA);
    VB = VA;
    VB.col(0).array() += 0.25;
    FB = FA;

    bool threw = false;
    try {
        PompeiuHausdorff ida(
            VA, FA, VB, FB, 1e-6, 1.0001, true,
            phd::search::SearchEngineType::IDAStar);
    } catch (const std::runtime_error&) {
        threw = true;
    }
    require(threw, "Expected std::runtime_error when max_factor limit is exceeded");
    std::cout << "[PASS] test_safety_limit_throws\n";
}

} // namespace

int main()
{
    try {
        test_identical_mesh();
        test_translated_cube_analytical();
        test_icosphere_refinement();
        test_official_107100_parity_and_cache();
        test_safety_limit_throws();
        std::cout << "All IDA* parity tests passed.\n";
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "TEST FAILURE: " << ex.what() << "\n";
        return 1;
    }
}
