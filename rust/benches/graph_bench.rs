use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use high_agent::{DirectedGraph, Node, Edge, GraphSnapshot};

fn create_test_graph(n_nodes: usize, n_edges: usize) -> DirectedGraph {
    let mut g = DirectedGraph::new();
    for i in 0..n_nodes {
        let node = Node::new(format!("fn_{}", i), format!("mod_{}", i % 4), format!("src/mod_{}.rs", i % 4));
        g.add_node(node);
    }
    for i in 0..n_edges {
        let from_idx = i % n_nodes;
        let to_idx = (i + 1) % n_nodes;
        let edge = Edge::new(format!("fn_{}", from_idx), format!("fn_{}", to_idx));
        edge.set_weight(1.0 + (i % 3) as f64 * 0.5);
        g.add_edge(edge);
    }
    g
}

pub fn bench_modularity(c: &mut Criterion) {
    let sizes = [10, 50, 100, 500];
    let mut group = c.benchmark_group("modularity");
    for size in sizes {
        let g = create_test_graph(size, size * 2);
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| black_box(&g).modularity());
        });
    }
    group.finish();
}

pub fn bench_phi(c: &mut Criterion) {
    let sizes = [10, 50, 100, 500];
    let mut group = c.benchmark_group("phi_computation");
    for size in sizes {
        let g = create_test_graph(size, size * 2);
        group.bench_with_input(BenchmarkId::from_parameter(size), &size, |b, _| {
            b.iter(|| black_box(&g).phi(1.0, 0.6, 0.4));
        });
    }
    group.finish();
}

pub fn bench_snapshot(c: &mut Criterion) {
    let g = create_test_graph(100, 200);
    c.bench_function("snapshot", |b| {
        b.iter(|| black_box(&g).snapshot());
    });
}

pub fn bench_pagerank(c: &mut Criterion) {
    let g = create_test_graph(100, 200);
    c.bench_function("pagerank", |b| {
        b.iter(|| black_box(&g).node_importance(20));
    });
}

pub fn bench_hotspots(c: &mut Criterion) {
    let g = create_test_graph(100, 200);
    c.bench_function("hotspots", |b| {
        b.iter(|| black_box(&g).hot_spots(5.0));
    });
}

pub fn bench_coupling_violations(c: &mut Criterion) {
    let g = create_test_graph(100, 200);
    c.bench_function("coupling_violations", |b| {
        b.iter(|| black_box(&g).coupling_violations());
    });
}

pub fn bench_regime_switch(c: &mut Criterion) {
    let mut g = create_test_graph(50, 100);
    c.bench_function("regime_switch", |b| {
        b.iter(|| {
            g.simulate_task(black_box("refactor"));
        });
    });
}

criterion_group!(
    benches,
    bench_modularity,
    bench_phi,
    bench_snapshot,
    bench_pagerank,
    bench_hotspots,
    bench_coupling_violations,
    bench_regime_switch,
);
criterion_main!(benches);
