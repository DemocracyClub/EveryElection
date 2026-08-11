# Tests

Writing tests for code that represents legislation is a bit fiddly.

Ideally we'd have perfect test cases but as noted in [Overview](./overview.md) there are concrete examples of a candidate rejecting their nomination, pushing back the publishing of the SoPN papers.

This project has two sets of tests:

* Unit tests, with single-specified examples
* Approval tests, with test data sourced from parsing historic SoPNs (provided by [Democracy Club](https://candidates.democracyclub.org.uk/), who maintain a database of candidates and elections)