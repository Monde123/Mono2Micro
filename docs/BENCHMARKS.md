# Empirical Benchmark Protocol & Evaluation

Mono2Micro benchmarks software decomposition tools using reproducible datasets, pinned git commits, and explicit ablation experiments.

## Evaluation Corpus
| Project | Stack | Pinned Commit SHA | Ground Truth Status |
|---|---|---|---|
| **jpetstore-6** | Java / MyBatis | `9780b6f9a0c78a3f81e058c4f923b75439c71a34` | Peer-reviewed ground truth (Hammad et al., 2023) |
| **daytrader-7** | Java EE / JPA | `e813a4bc037f59d4c2b9a764d8a230f81d9f0412` | IBM benchmark ground truth |
| **acmeair-nodejs** | Node.js / Express | `c432d1ef897d26456a2f8b4887b8d009fa12e67a` | Official IBM microservice decomposition |
| **plants-by-websphere** | Java / Spring | `fa9201bd4812f829f0e6988891d2938d2f10b83e` | WebSphere reference architecture |
| **ecommerce-fastapi** | Python / SQLAlchemy | `b89102cfa17b4c9201ef82a74c104279ab834190` | Surrogate metrics declared |
| **taskhub-express** | Node.js / TypeScript | `d76412efb6123490aa15c7e390df038012bf821a` | Surrogate metrics declared |

## Evaluation Metrics
1. **Precision & Recall** (where ground truth is available):
   $$\text{Precision} = \frac{|P \cap GT|}{|P|}, \quad \text{Recall} = \frac{|P \cap GT|}{|GT|}$$
2. **Newman-Girvan Modularity $Q$**:
   Measures community separation quality in the dependency graph. Higher $Q$ indicates high intra-domain cohesion and low cross-domain coupling.
3. **Inter-Domain Coupling Ratio**:
   Fraction of dependency edge weights traversing domain boundaries versus total graph edge weights.
4. **Shared Tables Count**:
   Number of database tables accessed concurrently by multiple distinct services without an encapsulation facade.
5. **Devil's Advocate False Block Rate**:
   Frequency of inappropriate plan blocks on legitimate, safe refactoring steps.
6. **Efficiency**:
   Execution duration, token consumption, and cost (USD) per migration step.

## Ablation Protocol
Every benchmark project is evaluated under three distinct baselines:
- `HEURISTIC_ONLY`: Pure offline AST graph and Louvain modularity (0 tokens, $0.00).
- `LLM_ONLY_NO_TOOLS`: LLM provided file names without code graphs or data layer analysis.
- `HYBRID_AGENT`: Combined Mono2Micro pipeline (AST graph + SQL analysis + adversarial review + LLM semantic refinement).

Run the suite anytime using:
```bash
make bench
```
Results are saved to `benchmarks/results/` as timestamped JSON reports and Markdown summary tables.
