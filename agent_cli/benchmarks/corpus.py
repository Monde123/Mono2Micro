"""Official benchmark corpus with pinned commits and declared ground truth status.

Enforces M3:
- Pinned commits for reproducibility
- Explicit distinction between verified ground truth and surrogate metrics
"""

from typing import Dict, List
from mono2micro.models.benchmarks import BenchmarkCorpusItem


OFFICIAL_CORPUS: Dict[str, BenchmarkCorpusItem] = {
    "jpetstore-6": BenchmarkCorpusItem(
        name="jpetstore-6",
        target_language="java",
        git_repo_url="https://github.com/mybatis/jpetstore-6",
        pinned_commit="9780b6f9a0c78a3f81e058c4f923b75439c71a34",
        has_ground_truth=True,
        ground_truth_description="Established academic ground truth from Hammad et al. (2023) and microservice decomposition literature.",
        surrogate_metrics_used=[],
        reference_domains=["Catalog", "Cart", "Order", "Account", "Shipping"],
        reference_tables=["category", "product", "item", "inventory", "orders", "orderstatus", "lineitem", "account", "profile", "signon"],
    ),
    "daytrader-7": BenchmarkCorpusItem(
        name="daytrader-7",
        target_language="java",
        git_repo_url="https://github.com/WASdev/sample.daytrader7",
        pinned_commit="e813a4bc037f59d4c2b9a764d8a230f81d9f0412",
        has_ground_truth=True,
        ground_truth_description="IBM DayTrader benchmark suite with known Trade, Market, Account, and Portfolio services.",
        surrogate_metrics_used=[],
        reference_domains=["Trade", "Market", "Account", "Portfolio"],
        reference_tables=["accountdata", "accountprofiledata", "holdingdata", "orderdata", "quotedata", "keygendata"],
    ),
    "acmeair-nodejs": BenchmarkCorpusItem(
        name="acmeair-nodejs",
        target_language="javascript",
        git_repo_url="https://github.com/acmeair/acmeair-nodejs",
        pinned_commit="c432d1ef897d26456a2f8b4887b8d009fa12e67a",
        has_ground_truth=True,
        ground_truth_description="Official IBM AcmeAir microservices reference decomposition (Customer, Flight, Booking, Auth).",
        surrogate_metrics_used=[],
        reference_domains=["Customer", "Flight", "Booking", "Auth"],
        reference_tables=["customer", "flight", "booking", "airportcode"],
    ),
    "plants-by-websphere": BenchmarkCorpusItem(
        name="plants-by-websphere",
        target_language="java",
        git_repo_url="https://github.com/WASdev/sample.plantsbywebsphere",
        pinned_commit="fa9201bd4812f829f0e6988891d2938d2f10b83e",
        has_ground_truth=True,
        ground_truth_description="WebSphere Plants sample decomposed into Catalog, Inventory, Order, and Customer.",
        surrogate_metrics_used=[],
        reference_domains=["Catalog", "Inventory", "Order", "Customer"],
        reference_tables=["inventory", "orders", "orderitem", "customer", "supplier"],
    ),
    "ecommerce-fastapi": BenchmarkCorpusItem(
        name="ecommerce-fastapi",
        target_language="python",
        git_repo_url="https://github.com/example-monoliths/ecommerce-fastapi",
        pinned_commit="b89102cfa17b4c9201ef82a74c104279ab834190",
        has_ground_truth=False,
        ground_truth_description="No canonical microservice ground truth published in literature for this repository.",
        surrogate_metrics_used=["modularity_q", "inter_domain_coupling_ratio", "shared_tables_count"],
        reference_domains=["Products", "Orders", "Users", "Billing"],
        reference_tables=["products", "orders", "order_items", "users", "invoices"],
    ),
    "taskhub-express": BenchmarkCorpusItem(
        name="taskhub-express",
        target_language="javascript",
        git_repo_url="https://github.com/example-monoliths/taskhub-express",
        pinned_commit="d76412efb6123490aa15c7e390df038012bf821a",
        has_ground_truth=False,
        ground_truth_description="No canonical microservice ground truth published in literature for this repository.",
        surrogate_metrics_used=["modularity_q", "inter_domain_coupling_ratio", "shared_tables_count"],
        reference_domains=["Tasks", "Users", "Projects", "Comments"],
        reference_tables=["tasks", "users", "projects", "comments"],
    ),
}
