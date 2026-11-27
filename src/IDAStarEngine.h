#ifndef IDASTAR_ENGINE_H
#define IDASTAR_ENGINE_H

#include "DistanceSearchEngine.h"
#include <cstdint>
#include <stdexcept>

namespace phd {
namespace search {

/**
 * @brief Iterative Deepening Branch-and-Bound (IDA*) search engine.
 *
 * Provides memory-bounded Hausdorff distance search using depth-first
 * exploration with adaptive upper-bound thresholds and bounded shallow-depth
 * memoization to avoid redundant AABB and cascading bound evaluations.
 */
class IDAStarEngine : public DistanceSearchEngine {
public:
    /**
     * @brief Constructs the engine with the provided search context and configuration.
     *
     * @param context Immutable problem context and search configuration.
     * @param config Threshold policy and shallow memoization parameters.
     */
    explicit IDAStarEngine(
        const SearchContext& context,
        const IDAStarConfig& config = IDAStarConfig{});

    ~IDAStarEngine() override = default;

    void search() override;

    double get_lower_bound() const override;
    double get_upper_bound() const override;
    int get_number_of_vertices() const override;
    int get_number_of_faces() const override;
    double get_bound_time_ms() const override;

    uint64_t get_iterations() const;
    uint64_t get_cache_hits() const;
    uint64_t get_cache_misses() const;

private:
    SearchContext context_;
    IDAStarConfig config_;
    double lower_;
    double upper_max_;
    int number_of_vertices_;
    int number_of_faces_;
    double bound_time_ms_;
    uint64_t iterations_;
    uint64_t cache_hits_;
    uint64_t cache_misses_;
};

} // namespace search
} // namespace phd

#endif // IDASTAR_ENGINE_H
