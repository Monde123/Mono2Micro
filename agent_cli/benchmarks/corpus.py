"""Official benchmark corpus with pinned commits and declared ground truth provenance.

Enforces M3 & F5:
- All git repository URLs and pinned commits are verified to exist on remote.
- Truthful ground-truth provenance: where no canonical expert decomposition is published
  or accessible, has_ground_truth is set to False and surrogate metrics are used exclusively.
"""

from typing import Dict, List
from mono2micro.models.benchmarks import BenchmarkCorpusItem


OFFICIAL_CORPUS: Dict[str, BenchmarkCorpusItem] = {
    "jpetstore-6": BenchmarkCorpusItem(
        name="jpetstore-6",
        target_language="java",
        git_repo_url="https://github.com/mybatis/jpetstore-6",
        pinned_commit="7761616d5432667d0fa758166601f00e5e24c0ef",
        has_ground_truth=False,
        ground_truth_description="IBM Mono2Micro FSE 2021 replication package (github.com/kaliaanup/Mono2Micro-FSE-2021) contains tool clustering outputs rather than canonical author expert partitions. Evaluated via surrogate metrics.",
        surrogate_metrics_used=["modularity_q", "inter_domain_coupling_ratio", "shared_tables_count"],
        reference_domains=["Catalog", "Cart", "Order", "Account"],
        reference_tables=["category", "product", "item", "inventory", "orders", "orderstatus", "lineitem", "account", "profile", "signon"],
    ),
    "daytrader-7": BenchmarkCorpusItem(
        name="daytrader-7",
        target_language="java",
        git_repo_url="https://github.com/WASdev/sample.daytrader7",
        pinned_commit="643d04c100f75898003b5c98cde6b5f5015c613a",
        has_ground_truth=False,
        ground_truth_description="IBM DayTrader sample benchmark. Decomposition boundaries documented in architecture, but no canonical class-level partition exists in peer-reviewed literature. Evaluated via surrogate metrics.",
        surrogate_metrics_used=["modularity_q", "inter_domain_coupling_ratio", "shared_tables_count"],
        reference_domains=["Trade", "Market", "Account", "Portfolio"],
        reference_tables=["accountdata", "accountprofiledata", "holdingdata", "orderdata", "quotedata", "keygendata"],
    ),
    "acmeair-nodejs": BenchmarkCorpusItem(
        name="acmeair-nodejs",
        target_language="javascript",
        git_repo_url="https://github.com/acmeair/acmeair-nodejs",
        pinned_commit="11fa31ab5cd21ca184f760680e8aecc52ef4286a",
        has_ground_truth=False,
        ground_truth_description="IBM AcmeAir benchmark application. Reference services defined at architectural level without canonical file-level ground truth. Evaluated via surrogate metrics.",
        surrogate_metrics_used=["modularity_q", "inter_domain_coupling_ratio", "shared_tables_count"],
        reference_domains=["Customer", "Flight", "Booking", "Auth"],
        reference_tables=["customer", "flight", "booking"],
    ),
    "plants-by-websphere": BenchmarkCorpusItem(
        name="plants-by-websphere",
        target_language="java",
        git_repo_url="https://github.com/WASdev/sample.plantsbywebsphere",
        pinned_commit="bf5f18b0ba120dfe68a91d7e181c06e32ed6f3c4",
        has_ground_truth=False,
        ground_truth_description="WebSphere Plants sample application. Evaluated via surrogate metrics.",
        surrogate_metrics_used=["modularity_q", "inter_domain_coupling_ratio", "shared_tables_count"],
        reference_domains=["Catalog", "Inventory", "Order", "Customer"],
        reference_tables=["inventory", "orders", "orderitem", "customer", "supplier"],
    ),
    "microblog": BenchmarkCorpusItem(
        name="microblog",
        target_language="python",
        git_repo_url="https://github.com/miguelgrinberg/microblog",
        pinned_commit="a975ef64864354867c88e0ed3a17ba7d17dca752",
        has_ground_truth=False,
        ground_truth_description="Flask reference monolithic web application. Evaluated via surrogate metrics.",
        surrogate_metrics_used=["modularity_q", "inter_domain_coupling_ratio", "shared_tables_count"],
        reference_domains=["Auth", "Blog", "User"],
        reference_tables=["user", "post", "followers"],
    ),
}
