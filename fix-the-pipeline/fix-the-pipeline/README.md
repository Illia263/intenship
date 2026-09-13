# Fix that, what is already in prod



**Time:** 2 weeks
**Handing over:** one PR + `POSTMORTEM.md`

---

## Legend



You went out to work on monday.

There is a pipeline, which loads taxi trips into Postgres. An intern wrote it, it is three months in prod, and everything suited everyone — until three things happened. The intern is not there.

Dashboard `dashboard_daily_revenue` reads the table `trips` right now. It is being used. Your task — **not to rewrite from zero**. Doing so is not allowed. Your task — to understand, what is broken, and fix it so, that the dashboard didn't notice.

---

## Launch



Needed: Docker, Docker Compose, Python 3.12+, ~8 GB of free disk, internet one time.

```bash
git clone <repo> && cd fix-the-pipeline
python -m venv .venv && source .venv/bin/activate
make setup          # downloads TLC data, raises Postgres. First time ~10 min.

```

Check, that everything is alive:

```bash
make psql
taxi=# \dt
taxi=# select count(*) from trips;    -- 0, this is normal

python etl.py                          # launch as is. Look, what will be.

```

What appeared after `make setup`:

```
source/                 13 CSV: 12 months 2024 + yellow_tripdata_2024-06-broken.csv
expected/reference.csv  reference amounts by months. With them you will check yourself.
etl.py                  that, what is in prod
schema.sql              schema, which the intern left

```

`source/` is distributed by HTTP on `localhost:8000` — this is the "source". Yes, this is `http.server` on top of the directory. But to address to it is needed by HTTP exactly because, that by HTTP there are timeouts and broken connections.

---

## Three incidents



Each — a real ticket from the tracker.

### INC-1. "Dashboard shows 8 mln trips for march. There were 3 mln of them"



On march 12 the job was falling by timeout. The on-duty restarted three times. Data tripled. Now in the table lies a mixture, and nobody knows, which rows are real.

**Needed:** to make it so, that a restart could not repeat this. And to remove existing duplicates, not stopping the dashboard.

### INC-2. "Needed to reload january. The source reissued the file"



Launched — poured in the current month. One more time — again current. The job physically doesn't know how to load the past.

**Needed:** `--month 2024-01` and `--backfill 2024-01:2024-12`.

### INC-3. "Accounting says, revenue for february diverges by 340 zloty"



The difference is small, stable, grows with volume. Nobody knows from where.

**Needed:** to find the reason, to prove with a test, to fix.

```bash
make check-money    # will show both numbers

```

---

## Requirements



1. `python etl.py --month 2024-01`

2. `python etl.py --backfill 2024-01:2024-12`

3. Repeated launch for the same month does not duplicate data


4. Every rejected row — into dead-letter with a reason


5. Rejected > 5% → we fall, and **do not leave partial data**

6. RSS < 500 MB on any quantity of months


7. 500k rows < 60 s


8. Structured logs with `run_id`

9. Exit codes: 0 — ok, 1 — data is bad, 2 — infrastructure



---

## Acceptance criteria



This is not "by eye". These are commands.

```bash
make check-idempotent     # diff must be empty
make check-memory         # Maximum resident set size < 500000 kbytes
make check-money          # two numbers must converge to a kopeck

```

```bash
# Partial data
make reset
python etl.py --month 2024-06-broken
echo $?                                          # 1
make psql -c "select count(*) from trips"        # 0, not 350000

# Dead-letter
wc -l dead_letter/dt=2024-06/*.ndjson
head -1 dead_letter/dt=2024-06/*.ndjson | jq .reason

# Backfill
make reset && python etl.py --backfill 2024-01:2024-12
# 12 rows, each with its own month:
make psql -c "select date_trunc('month', pickup) m, count(*) from trips group by 1 order by 1"

```

---

## Main artifact: `POSTMORTEM.md`

Code — half of the work.

| # | What I found | How it would manifest in prod | Why it happened so | Fix | Regress test |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

Rules:

* **Symptom — not "code is bad".** "float for money" — not a symptom. "Revenue for february diverges by 340 zloty, and the discrepancy grows with volume" — symptom.


* **Every fix has a test.** Without a test this is not a fix, but a hope.


* **Minimum one row "found, but didn't touch"** — with an explanation, why right now it's not worth it.



In the pipeline there are more problems, than three incidents. How many — I will not say. In prod also nobody says.

---

## Forbidden



* To rewrite from zero. To change the schema is allowed — but with migration, the dashboard must survive.


* To treat a symptom. `DISTINCT` in a view on top of doubles — not a fix of INC-1.


* `except Exception: pass` in any form, including `logger.warning` and `continue`.


* To optimize the unmeasured. In PR there must be a number "before" and "after".



---

## Rubric (100)



|  | Points |
| --- | --- |
| Three incidents closed, reasons named correctly | 30 |
| Found problems, about which they didn't ask | 20 |
| Every fix has a regress test | 20 |
| Acceptance criteria pass on a foreign machine | 15 |
| POSTMORTEM is read by a person, who didn't see the code | 15 |
|  |  |

**Fail independently from points:**

* idempotency "proven" with words, and not `make check-idempotent`

* money remained `float`

* in POSTMORTEM is written "rewrote, now works"



---

# Material part



Read **under the task**, and not in a row. Every block corresponds to a specific problem, which you will meet.

## When it bumps into memory (requirement 6)



Symptom: `--backfill 2024-01:2024-12` eats 12 GB and OOM killer kills it.

* David Beazley, **Generator Tricks for Systems Programmers** — [https://www.dabeaz.com/generators/](https://www.google.com/search?q=https://www.dabeaz.com/generators/)


The only thing, which is needed to read entirely. Slides 1–40 — exactly your case.


* `itertools` — [https://docs.python.org/3/library/itertools.html](https://docs.python.org/3/library/itertools.html) (`islice`, `chain`)


* `tracemalloc` — [https://docs.python.org/3/library/tracemalloc.html](https://docs.python.org/3/library/tracemalloc.html)

* Fluent Python, Ramalho, chapter 17 (iterators and generators)



Trap: `tracemalloc` sees only the memory of Python-allocator. Real RSS of the process — `/usr/bin/time -v` or `psutil`. The difference will surprise you, when you will reach parquet.

## When it bumps into money (INC-3)



```python
>>> 0.1 + 0.2
0.30000000000000004

```

Further it should reach by itself. If it doesn't reach:

* **What Every Computer Scientist Should Know About Floating-Point** — [https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html](https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html) (first 3 pages, the rest — for later)


* `decimal` — [https://docs.python.org/3/library/decimal.html](https://docs.python.org/3/library/decimal.html)

* PostgreSQL, numeric types — [https://www.postgresql.org/docs/current/datatype-numeric.html](https://www.postgresql.org/docs/current/datatype-numeric.html)


Read the paragraph about `numeric` vs `double precision`. There with plain text is written, what to do with money.



Question, to which you must answer in POSTMORTEM: why the discrepancy is **stable**, and not random?

## When it bumps into idempotency (INC-1, INC-2)



This is the most important part of the task. The rest — technicalities.

* **Fundamentals of Data Engineering**, Reis & Housley — chapter 5 (Data Generation) and 8 (Queries, Modeling)


* Idempotency in data-pipelines: [https://www.startdataengineering.com/post/why-how-idempotent-data-pipeline/](https://www.startdataengineering.com/post/why-how-idempotent-data-pipeline/)

* `INSERT ... ON CONFLICT` — [https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT](https://www.google.com/search?q=https://www.postgresql.org/docs/current/sql-insert.html%23SQL-ON-CONFLICT)

* Atomic file operations: `os.rename` — POSIX guarantees atomicity in borders of one FS. This is your friend for the criterion "not to leave partial data".



Question: you have `INSERT ... ON CONFLICT DO NOTHING`. By what key? In output data there is no `trip_id`. What will you do?

## When it bumps into speed of loading (requirement 7)



Symptom: 500k `INSERT` are executed 25 minutes.

* `COPY` — [https://www.postgresql.org/docs/current/sql-copy.html](https://www.postgresql.org/docs/current/sql-copy.html)

* `psycopg2.copy_expert` — [https://www.psycopg.org/docs/cursor.html#cursor.copy_expert](https://www.google.com/search?q=https://www.psycopg.org/docs/cursor.html%23cursor.copy_expert)

* Why `INSERT` in a loop is slow: each — a separate round-trip to the server + separate WAL-record. `COPY` — one stream.



Measure **before** and **after**. The number in PR.

## When it bumps into broken rows (requirements 4, 5)



* Hierarchy of exceptions — [https://docs.python.org/3/library/exceptions.html#exception-hierarchy](https://www.google.com/search?q=https://docs.python.org/3/library/exceptions.html%23exception-hierarchy)


Look, what exactly `except Exception` catches. And what it doesn't catch.


* `raise ... from` — [https://docs.python.org/3/tutorial/errors.html#exception-chaining](https://www.google.com/search?q=https://docs.python.org/3/tutorial/errors.html%23exception-chaining)

* Dead Letter Queue, pattern — [https://learn.microsoft.com/en-us/azure/architecture/patterns/](https://learn.microsoft.com/en-us/azure/architecture/patterns/)


(search for Dead Letter Channel; the concept is the same, realization at yours — a file)



Question: `except Exception: pass` catches also `KeyboardInterrupt`? And `MemoryError`? Check, do not guess.

## When it bumps into HTTP (requirement 9)



* `requests`, handling of errors — [https://requests.readthedocs.io/en/latest/user/quickstart/#errors-and-exceptions](https://www.google.com/search?q=https://requests.readthedocs.io/en/latest/user/quickstart/%23errors-and-exceptions)


Pay attention: `requests.get()` **doesn't throw an exception on 404**. `r.content` silently will return HTML of the error page.


* **Exponential Backoff and Jitter**, AWS — [https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)


Read about full jitter. This is that article, after which it becomes understandable, why retry without jitter is worse than absence of retry.


* `tenacity` — [https://tenacity.readthedocs.io/](https://tenacity.readthedocs.io/)


## When it bumps into logs (requirement 8)



* `logging` cookbook — [https://docs.python.org/3/howto/logging-cookbook.html](https://docs.python.org/3/howto/logging-cookbook.html)

* `contextvars` — [https://docs.python.org/3/library/contextvars.html](https://docs.python.org/3/library/contextvars.html)


This is the answer to the question "how to drag `run_id` through 8 levels of stack, not passing by argument".


* `structlog` — [https://www.structlog.org/](https://www.structlog.org/)


## When it bumps into SQL-injection



Look carefully at this row:

```python
cur.execute("INSERT INTO trips VALUES (%s, '%s', %s, %s)" % (...))

```

* [https://www.psycopg.org/docs/usage.html#the-problem-with-the-query-parameters](https://www.google.com/search?q=https://www.psycopg.org/docs/usage.html%23the-problem-with-the-query-parameters)


First paragraph. Red frame. Read twice.



## General, to read in parallel



* **Fundamentals of Data Engineering**, Reis & Housley — map of the locality. By 20 pages a day.


* **Designing Data-Intensive Applications**, Kleppmann — chapter 3 and 11. Not now, but soon.



---

## How I will check



1. I clone your PR onto a clean machine.


2. `make setup && make check-idempotent && make check-memory && make check-money`.


3. I read POSTMORTEM. If after it I do not understand, what was broken — fail, even if the code is flawless.


4. I pose the question "and what else?" for every your fix.



Questions, for which prepare:

* You fixed `datetime.now()`. What else in this file is executed in a moment, which you do not control?


* The process is killed by `kill -9` between the recording of the file and the commit into the DB. What is in the system?


* Your `ON CONFLICT` works. What will happen, if the source reissues the file with fixed amounts?


* Why the discrepancy in money was stable?
