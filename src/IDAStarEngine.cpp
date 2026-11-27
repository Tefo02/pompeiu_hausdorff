#include "IDAStarEngine.h"
#include "geometric_bounds.h"
#include "subdivision.h"
#include "telemetry.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <climits>
#include <cmath>
#include <cstdint>
#include <limits>
#include <unordered_map>

namespace phd {
namespace search {

namespace {

struct TriangleNode {
    Eigen::Matrix<double, 3, 3, Eigen::RowMajor> V;
    Eigen::Vector3d DV;
    Eigen::Vector3i I;
    Eigen::Matrix<double, 3, 3, Eigen::RowMajor> C;
    double upper_bound;
};

struct CachedSubdivisionEntry {
    Eigen::Matrix<double, 3, 3, Eigen::RowMajor> midpoints;
    Eigen::Vector3d DV_mid;
    Eigen::Vector3i I_mid;
    Eigen::Matrix<double, 3, 3, Eigen::RowMajor> C_mid;
    Eigen::Vector4d upper_children;
};

struct DeferredStats {
    static constexpr int kNumBuckets = 8;
    std::array<uint64_t, kNumBuckets> buckets{};
    uint64_t count = 0;
    double range_low = 0.0;
    double range_high = 0.0;

    void reset(double low, double high) {
        buckets.fill(0);
        count = 0;
        range_low = low;
        range_high = high;
    }

    void record(double bound) {
        count++;
        const double span = range_high - range_low;
        if (span <= 0.0) {
            buckets[kNumBuckets - 1]++;
            return;
        }
        const double normalized = (bound - range_low) / span;
        int idx = static_cast<int>(normalized * kNumBuckets);
        idx = std::max(0, std::min(kNumBuckets - 1, idx));
        buckets[idx]++;
    }
};

struct DfsContext {
    const SearchContext& search_context;
    const IDAStarConfig& config;
    double& lower;
    double tol_scaled;
    int max_depth;
    int max_allowed_vertices;
    int max_allowed_faces;
    uint64_t& subdivided_faces;
    int& number_of_vertices;
    int& number_of_faces;
    phd::geometry::BoundCallStatistics& bound_stats;
    phd::geometry::KangWorkspace& workspace;
    std::unordered_map<uint64_t, CachedSubdivisionEntry>& shallow_cache;
    uint64_t& cache_hits;
    uint64_t& cache_misses;
};

inline uint64_t make_cache_key(int root_face_idx, uint64_t path_code) {
    return (static_cast<uint64_t>(root_face_idx) << 16) | (path_code & 0xFFFFULL);
}

double select_next_threshold(
    double lower,
    double upper_max,
    double tol_scaled,
    const DeferredStats& prev_stats,
    const IDAStarConfig& config)
{
    const double gap = upper_max - lower;
    const double max_safe = std::nextafter(
        upper_max, -std::numeric_limits<double>::infinity());
    const double min_safe = std::min(lower + tol_scaled, max_safe);

    if (config.threshold_policy == ThresholdPolicy::NextBest) {
        return max_safe;
    }

    double decay = config.initial_decay_factor;
    if (config.threshold_policy == ThresholdPolicy::AdaptiveHistogram &&
        prev_stats.count > 0 &&
        prev_stats.range_high > prev_stats.range_low) {
        // Locate the upper quartile (top 25% mass) of deferred bounds from the prior pass
        const uint64_t target_mass = std::max<uint64_t>(1, prev_stats.count / 4);
        uint64_t accum = 0;
        int q75_bucket = DeferredStats::kNumBuckets - 1;
        for (int b = DeferredStats::kNumBuckets - 1; b >= 0; --b) {
            accum += prev_stats.buckets[b];
            if (accum >= target_mass) {
                q75_bucket = b;
                break;
            }
        }
        const double bin_width =
            (prev_stats.range_high - prev_stats.range_low) / DeferredStats::kNumBuckets;
        const double q75_bound = prev_stats.range_low + q75_bucket * bin_width;
        const double adaptive_ratio = (gap > 0.0) ? ((upper_max - q75_bound) / gap) : config.initial_decay_factor;
        decay = std::max(config.min_decay_factor, std::min(config.max_decay_factor, adaptive_ratio));
    }

    const double step = std::max(tol_scaled, gap * decay);
    const double candidate = upper_max - step;
    return std::max(min_safe, std::min(max_safe, candidate));
}

void dfs_branch(
    DfsContext& ctx,
    const TriangleNode& node,
    int root_face_idx,
    int depth,
    uint64_t path_code,
    double current_threshold,
    double& next_threshold,
    DeferredStats& deferred_stats)
{
    // 1. Permanent pruning against current global lower bound (strict inequality)
    if (node.upper_bound < ctx.lower) {
        return;
    }

    // 2. Iterative pruning: defer branches with upper bound at or below threshold
    if (node.upper_bound <= current_threshold) {
        if (node.upper_bound > next_threshold) {
            next_threshold = node.upper_bound;
        }
        deferred_stats.record(node.upper_bound);
        return;
    }

    // 3. Stopping criterion: tolerance satisfied for this triangle
    if (node.upper_bound - ctx.lower <= ctx.tol_scaled) {
        if (node.upper_bound > next_threshold) {
            next_threshold = node.upper_bound;
        }
        return;
    }

    // 4. Safety limits on recursion depth and total elements
    if (depth >= ctx.max_depth) {
        throw std::runtime_error("Exceeded maximum recursion depth before satisfying tolerance");
    }
    if (ctx.number_of_vertices + 3 > ctx.max_allowed_vertices ||
        ctx.number_of_faces + 4 > ctx.max_allowed_faces) {
        throw std::runtime_error("Exceeded maximum number of faces or vertices");
    }

    // 5. Midpoint 1-to-4 subdivision (always deterministic)
    const auto subdivision_result = phd::geometry::subdivide_triangle_1_to_4(
        node.V.row(0), node.V.row(1), node.V.row(2));
    ctx.subdivided_faces++;
    ctx.number_of_vertices += 3;
    ctx.number_of_faces += 4;

    Eigen::Vector3d DV_mid;
    Eigen::Vector3i I_mid;
    Eigen::Matrix<double, 3, 3, Eigen::RowMajor> C_mid;
    Eigen::Vector4d upper_children;

    const bool use_cache = (ctx.config.max_cache_depth > 0) &&
                           (depth < ctx.config.max_cache_depth) &&
                           (depth <= 7);
    bool cache_hit = false;

    if (use_cache) {
        const uint64_t key = make_cache_key(root_face_idx, path_code);
        const auto it = ctx.shallow_cache.find(key);
        if (it != ctx.shallow_cache.end()) {
            cache_hit = true;
            ctx.cache_hits++;
            DV_mid = it->second.DV_mid;
            I_mid = it->second.I_mid;
            C_mid = it->second.C_mid;
            upper_children = it->second.upper_children;
            ctx.lower = std::max(ctx.lower, DV_mid.maxCoeff());
        } else {
            ctx.cache_misses++;
        }
    }

    if (!cache_hit) {
        ctx.search_context.treeB.squared_distance(
            ctx.search_context.VB,
            ctx.search_context.FB,
            subdivision_result.midpoints,
            DV_mid,
            I_mid,
            C_mid);
        DV_mid = DV_mid.cwiseSqrt();

        // Monotonically increase global lower bound
        ctx.lower = std::max(ctx.lower, DV_mid.maxCoeff());

        Eigen::Matrix<double, 6, 3, Eigen::RowMajor> VA_eval;
        Eigen::Matrix<double, 6, 3, Eigen::RowMajor> C_eval;
        Eigen::Matrix<double, 6, 1> DV_eval;
        Eigen::Matrix<int, 6, 1> I_eval;

        VA_eval.row(0) = node.V.row(0);
        VA_eval.row(1) = node.V.row(1);
        VA_eval.row(2) = node.V.row(2);
        VA_eval.block<3, 3>(3, 0) = subdivision_result.midpoints;

        C_eval.row(0) = node.C.row(0);
        C_eval.row(1) = node.C.row(1);
        C_eval.row(2) = node.C.row(2);
        C_eval.block<3, 3>(3, 0) = C_mid;

        DV_eval(0) = node.DV(0);
        DV_eval(1) = node.DV(1);
        DV_eval(2) = node.DV(2);
        DV_eval.segment<3>(3) = DV_mid;

        I_eval(0) = node.I(0);
        I_eval(1) = node.I(1);
        I_eval(2) = node.I(2);
        I_eval.segment<3>(3) = I_mid;

        Eigen::Vector4i success_children;
        if (!phd::geometry::evaluate_cascading_bounds(
                VA_eval,
                subdivision_result.local_faces,
                ctx.search_context.VB,
                ctx.search_context.FB,
                DV_eval,
                I_eval,
                C_eval,
                ctx.lower,
                upper_children,
                success_children,
                &ctx.workspace,
                &ctx.bound_stats)) {
            throw std::runtime_error("error in upper bound function during IDA* search");
        }

        if (use_cache && ctx.shallow_cache.size() < ctx.config.max_cache_entries) {
            const uint64_t key = make_cache_key(root_face_idx, path_code);
            ctx.shallow_cache.emplace(
                key,
                CachedSubdivisionEntry{
                    subdivision_result.midpoints,
                    DV_mid,
                    I_mid,
                    C_mid,
                    upper_children});
        }
    }

    // Prepare vertex attributes for child node construction
    Eigen::Matrix<double, 6, 3, Eigen::RowMajor> VA_children;
    Eigen::Matrix<double, 6, 3, Eigen::RowMajor> C_children;
    Eigen::Matrix<double, 6, 1> DV_children;
    Eigen::Matrix<int, 6, 1> I_children;

    VA_children.row(0) = node.V.row(0);
    VA_children.row(1) = node.V.row(1);
    VA_children.row(2) = node.V.row(2);
    VA_children.block<3, 3>(3, 0) = subdivision_result.midpoints;

    C_children.row(0) = node.C.row(0);
    C_children.row(1) = node.C.row(1);
    C_children.row(2) = node.C.row(2);
    C_children.block<3, 3>(3, 0) = C_mid;

    DV_children(0) = node.DV(0);
    DV_children(1) = node.DV(1);
    DV_children(2) = node.DV(2);
    DV_children.segment<3>(3) = DV_mid;

    I_children(0) = node.I(0);
    I_children(1) = node.I(1);
    I_children(2) = node.I(2);
    I_children.segment<3>(3) = I_mid;

    // Sort children in descending order of upper bound to raise lower_ earlier
    std::array<int, 4> order = {{0, 1, 2, 3}};
    std::sort(order.begin(), order.end(), [&](int a, int b) {
        return upper_children(a) > upper_children(b);
    });

    for (int c : order) {
        if (upper_children(c) >= ctx.lower) {
            TriangleNode child_node;
            for (int k = 0; k < 3; ++k) {
                const int idx = subdivision_result.local_faces(c, k);
                child_node.V.row(k) = VA_children.row(idx);
                child_node.DV(k) = DV_children(idx);
                child_node.I(k) = I_children(idx);
                child_node.C.row(k) = C_children.row(idx);
            }
            child_node.upper_bound = upper_children(c);

            const uint64_t child_path_code = use_cache
                ? ((path_code << 2) | static_cast<uint64_t>(c))
                : 0ULL;
            dfs_branch(
                ctx,
                child_node,
                root_face_idx,
                depth + 1,
                child_path_code,
                current_threshold,
                next_threshold,
                deferred_stats);
        }
    }
}

} // anonymous namespace

IDAStarEngine::IDAStarEngine(
    const SearchContext& context,
    const IDAStarConfig& config)
    : context_(context)
    , config_(config)
    , lower_(context.initial_lower)
    , upper_max_(context.initial_upper.maxCoeff())
    , number_of_vertices_(context.VA.rows())
    , number_of_faces_(context.FA.rows())
    , bound_time_ms_(0.0)
    , iterations_(0)
    , cache_hits_(0)
    , cache_misses_(0)
{
}

void IDAStarEngine::search()
{
    const double start_time = std::chrono::duration<double>(
        std::chrono::system_clock::now().time_since_epoch()).count();

    uint64_t subdivided_faces = 0;
    phd::geometry::BoundCallStatistics search_bound_stats;
    phd::geometry::KangWorkspace kang_workspace;
    std::unordered_map<uint64_t, CachedSubdivisionEntry> shallow_cache;
    if (config_.max_cache_depth > 0 && config_.max_cache_entries > 0) {
        shallow_cache.reserve(std::min<std::size_t>(config_.max_cache_entries, 4096));
    }

    lower_ = context_.initial_lower;
    upper_max_ = context_.initial_upper.maxCoeff();
    iterations_ = 0;
    cache_hits_ = 0;
    cache_misses_ = 0;

    const double tol_scaled = context_.tol * context_.dA;
    const int max_allowed_vertices = (context_.max_factor * context_.VA.rows() < INT_MAX)
        ? static_cast<int>(context_.max_factor * context_.VA.rows())
        : INT_MAX;
    const int max_allowed_faces = (context_.max_factor * context_.FA.rows() < INT_MAX)
        ? static_cast<int>(context_.max_factor * context_.FA.rows())
        : INT_MAX;
    const int max_depth = 100;

    auto construct_root_node = [&](int f) -> TriangleNode {
        TriangleNode node;
        for (int k = 0; k < 3; ++k) {
            const int v_idx = context_.FA(f, k);
            node.V.row(k) = context_.VA.row(v_idx);
            node.DV(k) = context_.initial_DV(v_idx);
            node.I(k) = context_.initial_I(v_idx);
            node.C.row(k) = context_.initial_C.row(v_idx);
        }
        node.upper_bound = context_.initial_upper(f);
        return node;
    };

    DfsContext ctx = {
        context_,
        config_,
        lower_,
        tol_scaled,
        max_depth,
        max_allowed_vertices,
        max_allowed_faces,
        subdivided_faces,
        number_of_vertices_,
        number_of_faces_,
        search_bound_stats,
        kang_workspace,
        shallow_cache,
        cache_hits_,
        cache_misses_
    };

    DeferredStats prev_deferred_stats;
    DeferredStats current_deferred_stats;

    while (upper_max_ - lower_ > tol_scaled) {
        iterations_++;
        number_of_vertices_ = context_.VA.rows();
        number_of_faces_ = context_.FA.rows();

        const double current_threshold = select_next_threshold(
            lower_, upper_max_, tol_scaled, prev_deferred_stats, config_);

        double next_threshold = -std::numeric_limits<double>::infinity();
        current_deferred_stats.reset(lower_, current_threshold);

        for (int f = 0; f < context_.FA.rows(); ++f) {
            const double root_upper = context_.initial_upper(f);
            if (root_upper < lower_) {
                continue;
            }
            if (root_upper <= current_threshold) {
                if (root_upper > next_threshold) {
                    next_threshold = root_upper;
                }
                current_deferred_stats.record(root_upper);
                continue;
            }

            TriangleNode root_node = construct_root_node(f);
            dfs_branch(
                ctx,
                root_node,
                f,
                0,
                1ULL,
                current_threshold,
                next_threshold,
                current_deferred_stats);
        }

        // If no unexpanded branch exceeded lower_ + tol_scaled, search has converged
        if (next_threshold <= lower_ + tol_scaled) {
            upper_max_ = std::max(lower_, next_threshold);
            break;
        }

        // Invariant: upper_max_ is a valid upper bound across all remaining unexpanded leaves
        upper_max_ = next_threshold;
        prev_deferred_stats = current_deferred_stats;

        if (upper_max_ - lower_ <= tol_scaled) {
            break;
        }
    }

    const double end_time = std::chrono::duration<double>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    bound_time_ms_ = 1000.0 * (end_time - start_time);

    phd::telemetry::record_search_metrics(subdivided_faces, search_bound_stats);
}

double IDAStarEngine::get_lower_bound() const
{
    return lower_;
}

double IDAStarEngine::get_upper_bound() const
{
    return upper_max_;
}

int IDAStarEngine::get_number_of_vertices() const
{
    return number_of_vertices_;
}

int IDAStarEngine::get_number_of_faces() const
{
    return number_of_faces_;
}

double IDAStarEngine::get_bound_time_ms() const
{
    return bound_time_ms_;
}

uint64_t IDAStarEngine::get_iterations() const
{
    return iterations_;
}

uint64_t IDAStarEngine::get_cache_hits() const
{
    return cache_hits_;
}

uint64_t IDAStarEngine::get_cache_misses() const
{
    return cache_misses_;
}

} // namespace search
} // namespace phd
