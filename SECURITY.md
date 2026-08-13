# Security Policy

## What Compost is today

Compost is an experimental local research tool. It is a command-line experiment that reads text files from local directories and writes a CSV.

There is no deployed service, no hosted API, no database, no user accounts and no network listener. Nothing in this repository processes data belonging to anyone but the person running it.

Please read the rest of this document with that scope in mind. The project makes no security guarantees it has not earned.

## Supported versions

There is one experimental main line. Only the current `main` receives fixes. Earlier commits are not maintained.

## Do not send us your data

Do not include any of the following in issues, pull requests, discussions or commits:

- credentials, tokens, API keys or other secrets;
- private, unpublished or confidential writing;
- documents belonging to an employer, client or third party;
- licensed, copyrighted or otherwise redistribution-restricted corpus material.

Raw corpus text is expected to stay on the machine that downloaded it. `.gitignore` excludes the corpus directories by default, but that is a convenience, not a control — it does not stop a deliberate `git add -f`, and it cannot help once something has been pushed to a public repository.

If you want to illustrate a pattern, a short constructed example sentence is enough. It usually makes the report clearer anyway.

## Reporting a vulnerability

Please report suspected vulnerabilities privately rather than opening a public issue.

If GitHub private vulnerability reporting is enabled on this repository, use the **Security** tab → **Report a vulnerability**. That is the preferred route: it keeps the report private until a fix exists, and it does not require the reporter to find a contact address.

If that option is not visible, open a public issue that states only that you have found a security-relevant problem and asks for a private channel. Do not include the details in the public issue.

Please do not include working exploit material or any real secret in a report. A description of the mechanism is sufficient.

## Scope

Realistic concerns for a repository at this stage:

- accidental publication of secrets or corpus material through Git history;
- a supply-chain problem reaching the repository through a dependency or workflow;
- a change to the extraction or scoring logic that silently corrupts results.

The last one is a research-integrity problem rather than a conventional vulnerability, but it is the failure most likely to matter here, and reports of it are welcome through the same private route.

## What we cannot promise

No service-level commitments, no response-time target and no bounty. This is an early-stage open research project maintained in spare time. Reports are read and taken seriously; that is the extent of the promise.
