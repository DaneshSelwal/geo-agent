# Performance Optimizaton
- Earth Engine synchronous I/O causes delays. When possible, batch multiple values like counts, statistics, and coverages into a single `ee.Dictionary` and invoke `.getInfo()` exactly once.
- Always use `ee.Algorithms.If` to avoid exceptions if an ee collection may be empty but still batch evaluations securely.
