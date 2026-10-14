# Hand-Labelled Detection Ground Truth

This directory contains human-checked architectural labels (routes, database entities/tables, and test frameworks) for a fixed set of real open-source applications representing distinct technology stacks:

1. `jpetstore-6.json`: Java + MyBatis + Spring MVC / Stripes + JUnit / Selenide.
2. `microblog.json`: Python + Flask + SQLAlchemy + Python unittest.
3. `acmeair-nodejs.json`: JavaScript + Express.js + Mongoose/MongoDB + Mocha.

## Methodology
- **Routes**: Manually inspected from route controllers, blueprints, and decorators (`@RequestMapping`, `@app.route`, `app.get/post`).
- **Entities & Tables**: Manually inspected from data model definitions, MyBatis XML mappers, and ORM schema classes.
- **Test Frameworks**: Verified by checking configuration files (`pom.xml`, `package.json`, test runner invocations).

## Review Status
All files are marked `FLAGGED_FOR_HUMAN_REVIEW` to guarantee peer review during pull requests.
