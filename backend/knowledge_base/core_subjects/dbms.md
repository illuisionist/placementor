# Database Management Systems (DBMS) — Comprehensive Interview Guide
> **PlaceMentor AI Knowledge Base** | Core Subjects | DBMS
> Covers: ER Model, Keys, SQL, JOINs, Normalization, ACID, Indexing, NoSQL, CAP, 20 SQL Queries

---

## Table of Contents
1. [ER Model](#1-er-model)
2. [Keys in DBMS](#2-keys-in-dbms)
3. [SQL — DDL & DML](#3-sql--ddl--dml)
4. [JOINs](#4-joins)
5. [Aggregate Functions, GROUP BY, HAVING](#5-aggregate-functions-group-by-having)
6. [Window Functions](#6-window-functions)
7. [Normalization](#7-normalization)
8. [ACID Properties](#8-acid-properties)
9. [Transaction Isolation Levels](#9-transaction-isolation-levels)
10. [Indexing](#10-indexing)
11. [NoSQL vs SQL](#11-nosql-vs-sql)
12. [CAP Theorem](#12-cap-theorem)
13. [20 Important SQL Queries](#13-20-important-sql-queries)

---

## 1. ER Model

The **Entity-Relationship (ER) Model** is a conceptual data model that describes data as entities, their attributes, and relationships.

### 1.1 Entities

- **Entity**: A real-world object or concept (e.g., `Student`, `Course`, `Employee`).
- **Entity Set**: Collection of similar entities.
- **Strong Entity**: Has its own primary key (e.g., `Employee`).
- **Weak Entity**: Depends on a strong entity; has no primary key of its own (e.g., `Dependent` depends on `Employee`). Identified by partial key + owner's key.

### 1.2 Attributes

| Attribute Type        | Description                                   | Example                        |
|-----------------------|-----------------------------------------------|--------------------------------|
| **Simple**            | Atomic, not divisible                         | `Age`, `Salary`               |
| **Composite**         | Made up of sub-attributes                     | `Name` = `(First, Middle, Last)` |
| **Multi-valued**      | Can have multiple values                      | `Phone_Numbers`               |
| **Derived**           | Computed from other attributes                | `Age` from `DOB`              |
| **Key Attribute**     | Uniquely identifies entity (underlined in ER) | `EmpID`                       |
| **Null Attribute**    | May have no value                             | `MiddleName`                  |

### 1.3 Relationships

- **Relationship**: Association between two or more entities.
- **Degree**: Number of entity sets participating.
  - Unary (recursive): Employee supervises Employee
  - Binary: Student enrolls in Course
  - Ternary: Doctor prescribes Medicine for Patient

### 1.4 Cardinality Ratios

| Type        | Notation | Meaning                                      | Example                          |
|-------------|----------|----------------------------------------------|----------------------------------|
| One-to-One  | 1:1      | One entity maps to exactly one               | Person ↔ Passport               |
| One-to-Many | 1:N      | One entity maps to many                      | Department → Employees           |
| Many-to-One | N:1      | Many entities map to one                     | Employees → Department           |
| Many-to-Many| M:N      | Many map to many (junction table needed)     | Students ↔ Courses               |

### 1.5 Participation Constraints
- **Total (mandatory)**: Every entity must participate — double line in ER diagram (e.g., every Employee MUST work in a Department).
- **Partial (optional)**: Some entities may not participate — single line (e.g., not every Employee manages a Department).

---

## 2. Keys in DBMS

| Key Type           | Definition                                                          | Example                          |
|--------------------|---------------------------------------------------------------------|----------------------------------|
| **Super Key**      | Any set of attributes that uniquely identifies a row               | `{EmpID}`, `{EmpID, Name}`       |
| **Candidate Key**  | Minimal super key (no redundant attributes)                        | `{EmpID}`, `{Email}`             |
| **Primary Key**    | Chosen candidate key; cannot be NULL                               | `EmpID`                         |
| **Alternate Key**  | Candidate keys not chosen as primary key                           | `Email` (if EmpID is PK)         |
| **Foreign Key**    | Attribute referencing primary key of another table                 | `DeptID` in Employee → Department|
| **Composite Key**  | Primary key made of two or more attributes                         | `(StudentID, CourseID)` in Enrollment|
| **Surrogate Key**  | System-generated artificial primary key                            | Auto-increment `id`              |

### Key Relationships
```
All Keys ⊃ Super Keys ⊃ Candidate Keys ⊃ { Primary Key, Alternate Keys }
```

---

## 3. SQL — DDL & DML

### 3.1 Data Definition Language (DDL)

DDL commands define and modify the **schema** (structure) of the database.

```sql
-- CREATE TABLE
CREATE TABLE Employees (
    EmpID     INT           PRIMARY KEY AUTO_INCREMENT,
    Name      VARCHAR(100)  NOT NULL,
    Email     VARCHAR(150)  UNIQUE,
    DeptID    INT,
    Salary    DECIMAL(10,2) DEFAULT 0.00,
    HireDate  DATE,
    FOREIGN KEY (DeptID) REFERENCES Departments(DeptID)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- ALTER TABLE — add column
ALTER TABLE Employees ADD COLUMN Phone VARCHAR(15);

-- ALTER TABLE — modify column type
ALTER TABLE Employees MODIFY COLUMN Salary DECIMAL(12,2);

-- ALTER TABLE — rename column
ALTER TABLE Employees RENAME COLUMN Phone TO MobileNo;

-- ALTER TABLE — drop column
ALTER TABLE Employees DROP COLUMN MobileNo;

-- ALTER TABLE — add constraint
ALTER TABLE Employees ADD CONSTRAINT chk_salary CHECK (Salary >= 0);

-- DROP TABLE (irreversible!)
DROP TABLE IF EXISTS Employees;

-- TRUNCATE (removes all rows, keeps structure)
TRUNCATE TABLE Employees;

-- CREATE INDEX
CREATE INDEX idx_emp_dept ON Employees(DeptID);

-- CREATE VIEW
CREATE VIEW HighEarners AS
    SELECT Name, Salary FROM Employees WHERE Salary > 100000;
```

### 3.2 Data Manipulation Language (DML)

DML commands manipulate **data** within existing tables.

```sql
-- INSERT single row
INSERT INTO Employees (Name, Email, DeptID, Salary, HireDate)
VALUES ('Alice Johnson', 'alice@corp.com', 3, 95000.00, '2022-01-15');

-- INSERT multiple rows
INSERT INTO Employees (Name, Email, DeptID, Salary, HireDate) VALUES
('Bob Smith',   'bob@corp.com',   2, 72000.00, '2021-06-01'),
('Carol White', 'carol@corp.com', 3, 110000.00, '2020-03-10'),
('David Lee',   'david@corp.com', 1, 65000.00, '2023-07-22');

-- INSERT from SELECT
INSERT INTO HighSalaryArchive (Name, Salary)
SELECT Name, Salary FROM Employees WHERE Salary > 100000;

-- UPDATE single column
UPDATE Employees SET Salary = Salary * 1.10 WHERE DeptID = 3;

-- UPDATE multiple columns
UPDATE Employees
SET Salary = 80000, DeptID = 2
WHERE EmpID = 4;

-- DELETE specific rows
DELETE FROM Employees WHERE HireDate < '2015-01-01';

-- DELETE all rows (keeps structure, unlike DROP)
DELETE FROM Employees;

-- SELECT with WHERE, ORDER BY, LIMIT
SELECT Name, Salary
FROM Employees
WHERE DeptID = 3
ORDER BY Salary DESC
LIMIT 5;
```

---

## 4. JOINs

JOINs combine rows from two or more tables based on related columns.

**Sample Tables:**

```sql
-- Employees table          -- Departments table
EmpID | Name    | DeptID    DeptID | DeptName
------|---------|-------    -------|----------
1     | Alice   | 10        10     | Engineering
2     | Bob     | 20        20     | Marketing
3     | Carol   | 10        30     | HR
4     | David   | NULL
```

### 4.1 INNER JOIN
Returns rows that have **matching values in both tables**.

```sql
SELECT e.Name, d.DeptName
FROM Employees e
INNER JOIN Departments d ON e.DeptID = d.DeptID;

-- Result:
-- Alice  | Engineering
-- Bob    | Marketing
-- Carol  | Engineering
-- (David excluded — NULL DeptID; HR excluded — no employees)
```

### 4.2 LEFT JOIN (LEFT OUTER JOIN)
Returns **all rows from left table** + matching rows from right. NULL where no match.

```sql
SELECT e.Name, d.DeptName
FROM Employees e
LEFT JOIN Departments d ON e.DeptID = d.DeptID;

-- Result:
-- Alice  | Engineering
-- Bob    | Marketing
-- Carol  | Engineering
-- David  | NULL          ← David included with NULL dept
```

### 4.3 RIGHT JOIN (RIGHT OUTER JOIN)
Returns **all rows from right table** + matching rows from left.

```sql
SELECT e.Name, d.DeptName
FROM Employees e
RIGHT JOIN Departments d ON e.DeptID = d.DeptID;

-- Result:
-- Alice  | Engineering
-- Carol  | Engineering
-- Bob    | Marketing
-- NULL   | HR            ← HR included with no employees
```

### 4.4 FULL OUTER JOIN
Returns **all rows from both tables**. NULL where no match on either side.

```sql
SELECT e.Name, d.DeptName
FROM Employees e
FULL OUTER JOIN Departments d ON e.DeptID = d.DeptID;

-- Result:
-- Alice  | Engineering
-- Carol  | Engineering
-- Bob    | Marketing
-- David  | NULL          ← from left (no dept)
-- NULL   | HR            ← from right (no employees)

-- MySQL workaround (no FULL OUTER JOIN):
SELECT e.Name, d.DeptName FROM Employees e LEFT JOIN Departments d ON e.DeptID = d.DeptID
UNION
SELECT e.Name, d.DeptName FROM Employees e RIGHT JOIN Departments d ON e.DeptID = d.DeptID;
```

### 4.5 CROSS JOIN
Returns the **Cartesian product** — every row from left paired with every row from right.

```sql
SELECT e.Name, d.DeptName
FROM Employees e
CROSS JOIN Departments d;

-- Result: 4 employees × 3 departments = 12 rows
-- (Alice, Engineering), (Alice, Marketing), (Alice, HR),
-- (Bob, Engineering), (Bob, Marketing), ...
```

### 4.6 SELF JOIN
Joining a table **with itself** (using aliases).

```sql
-- Find employee and their manager (both in same table)
-- Employees: EmpID, Name, ManagerID
SELECT e.Name AS Employee, m.Name AS Manager
FROM Employees e
LEFT JOIN Employees m ON e.ManagerID = m.EmpID;

-- Result:
-- Alice   | Carol      ← Alice's manager is Carol
-- Bob     | Carol
-- Carol   | NULL       ← Carol has no manager (CEO)
-- David   | Alice
```

### JOIN Summary Table

| JOIN Type        | Left Table Rows | Right Table Rows | NULL Filled |
|------------------|----------------|-----------------|-------------|
| INNER JOIN       | Matching only  | Matching only   | Never       |
| LEFT JOIN        | All            | Matching only   | Right side  |
| RIGHT JOIN       | Matching only  | All             | Left side   |
| FULL OUTER JOIN  | All            | All             | Both sides  |
| CROSS JOIN       | All            | All             | Never       |

---

## 5. Aggregate Functions, GROUP BY, HAVING

### 5.1 Aggregate Functions

| Function       | Description                        | Example                                |
|----------------|------------------------------------|----------------------------------------|
| `COUNT(*)`     | Count rows                         | `SELECT COUNT(*) FROM Employees`       |
| `COUNT(col)`   | Count non-NULL values              | `SELECT COUNT(DeptID) FROM Employees`  |
| `SUM(col)`     | Sum of values                      | `SELECT SUM(Salary) FROM Employees`    |
| `AVG(col)`     | Average value                      | `SELECT AVG(Salary) FROM Employees`    |
| `MAX(col)`     | Maximum value                      | `SELECT MAX(Salary) FROM Employees`    |
| `MIN(col)`     | Minimum value                      | `SELECT MIN(Salary) FROM Employees`    |
| `GROUP_CONCAT` | Concatenate group values (MySQL)   | `GROUP_CONCAT(Name SEPARATOR ', ')`    |

### 5.2 GROUP BY + HAVING

```sql
-- Count employees per department, show only depts with > 2 employees
SELECT DeptID, COUNT(*) AS EmployeeCount, AVG(Salary) AS AvgSalary
FROM Employees
WHERE Salary > 40000          -- WHERE filters BEFORE grouping
GROUP BY DeptID
HAVING COUNT(*) > 2           -- HAVING filters AFTER grouping
ORDER BY AvgSalary DESC;
```

> **Key Rule**: `WHERE` operates on rows → `GROUP BY` groups → `HAVING` filters groups.
> You cannot use aggregate functions in `WHERE`; use `HAVING` instead.

---

## 6. Window Functions

Window functions perform calculations **across a set of rows related to the current row** without collapsing them (unlike GROUP BY).

```sql
-- Syntax:
function_name() OVER (
    PARTITION BY column    -- optional: reset window per group
    ORDER BY column        -- defines row order within window
    ROWS/RANGE BETWEEN ... -- optional: frame specification
)
```

### 6.1 ROW_NUMBER, RANK, DENSE_RANK

```sql
SELECT Name, Salary, DeptID,
    ROW_NUMBER()  OVER (PARTITION BY DeptID ORDER BY Salary DESC) AS RowNum,
    RANK()        OVER (PARTITION BY DeptID ORDER BY Salary DESC) AS Rnk,
    DENSE_RANK()  OVER (PARTITION BY DeptID ORDER BY Salary DESC) AS DenseRnk
FROM Employees;

-- Salary: 110000, 95000, 95000, 72000 in Dept 10
-- ROW_NUMBER:  1, 2, 3, 4   (always unique)
-- RANK:        1, 2, 2, 4   (gap after tie)
-- DENSE_RANK:  1, 2, 2, 3   (no gap after tie)
```

### 6.2 LAG and LEAD

```sql
-- LAG: access previous row's value
SELECT Name, Salary,
    LAG(Salary, 1, 0) OVER (ORDER BY HireDate) AS PrevSalary,
    Salary - LAG(Salary, 1, 0) OVER (ORDER BY HireDate) AS SalaryDiff
FROM Employees;

-- LEAD: access next row's value
SELECT Name, HireDate,
    LEAD(HireDate, 1) OVER (ORDER BY HireDate) AS NextHireDate
FROM Employees;
```

### 6.3 Running Total with SUM() OVER

```sql
SELECT Name, HireDate, Salary,
    SUM(Salary) OVER (ORDER BY HireDate
                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS RunningTotal
FROM Employees;
```

---

## 7. Normalization

Normalization is the process of organizing a database to reduce **data redundancy** and improve **data integrity** by decomposing tables into smaller, well-structured ones.

### Functional Dependency (FD)
`A → B` means: if two rows have the same value for A, they must have the same value for B.
- A is the **determinant**, B is the **dependent**.

---

### 7.1 First Normal Form (1NF)

**Rule**: All attributes must be **atomic** (no multi-valued or composite attributes); every row must be unique.

**Violation Example:**
```
StudentCourses table (NOT in 1NF):
StudentID | Name  | Courses
----------|-------|-------------------
1         | Alice | Math, Physics, CS      ← multi-valued!
2         | Bob   | Chemistry
```

**Fix (1NF):**
```
StudentID | Name  | Course
----------|-------|----------
1         | Alice | Math
1         | Alice | Physics
1         | Alice | CS
2         | Bob   | Chemistry

PK = (StudentID, Course)
```

---

### 7.2 Second Normal Form (2NF)

**Rule**: Must be in 1NF + **No partial dependency** (no non-key attribute depends on part of a composite primary key).

**Violation Example:**
```
Enrollment table (1NF but NOT 2NF):
StudentID | CourseID | CourseName  | InstructorName | Grade
----------|----------|-------------|----------------|------
1         | C01      | Math        | Dr. Smith      | A
1         | C02      | Physics     | Dr. Jones      | B
2         | C01      | Math        | Dr. Smith      | A

PK = (StudentID, CourseID)
CourseName depends only on CourseID → PARTIAL DEPENDENCY violation!
```

**Fix (2NF) — Decompose:**
```sql
-- Courses table
CourseID | CourseName | InstructorName

-- Enrollment table
StudentID | CourseID | Grade
```

---

### 7.3 Third Normal Form (3NF)

**Rule**: Must be in 2NF + **No transitive dependency** (no non-key attribute depends on another non-key attribute).

**Violation Example:**
```
Employees table (2NF but NOT 3NF):
EmpID | Name  | DeptID | DeptName | DeptLocation
------|-------|--------|----------|-------------
1     | Alice | D01    | Eng      | Floor 3
2     | Bob   | D02    | Mktg     | Floor 2
3     | Carol | D01    | Eng      | Floor 3

EmpID → DeptID → DeptName  (TRANSITIVE dependency!)
EmpID → DeptID → DeptLocation
```

**Fix (3NF) — Decompose:**
```sql
-- Departments table
DeptID | DeptName | DeptLocation

-- Employees table
EmpID | Name | DeptID  (Foreign key)
```

---

### 7.4 Boyce-Codd Normal Form (BCNF)

**Rule**: Must be in 3NF + **For every FD X → Y, X must be a superkey**.
BCNF is stronger than 3NF — eliminates anomalies 3NF misses.

**Violation Example (in 3NF but NOT BCNF):**
```
CourseTeacher table:
Student | Course  | Teacher
--------|---------|--------
Alice   | Math    | Dr. Smith
Alice   | Physics | Dr. Jones
Bob     | Math    | Dr. Lee

FDs:
  (Student, Course) → Teacher  ← candidate key ✓
  Teacher → Course             ← Teacher is NOT a superkey → BCNF violation!
```

**Fix (BCNF):**
```sql
-- TeacherCourse
Teacher    | Course
-----------|--------
Dr. Smith  | Math
Dr. Jones  | Physics
Dr. Lee    | Math

-- StudentTeacher
Student | Teacher
--------|----------
Alice   | Dr. Smith
Alice   | Dr. Jones
Bob     | Dr. Lee
```

### Normalization Summary

| Normal Form | Requirement                                      | Eliminates                  |
|-------------|--------------------------------------------------|-----------------------------|
| 1NF         | Atomic values, unique rows                       | Multi-valued attributes      |
| 2NF         | 1NF + No partial dependencies                    | Partial dependency anomalies |
| 3NF         | 2NF + No transitive dependencies                 | Transitive dependency issues |
| BCNF        | 3NF + Every determinant is a superkey            | Remaining anomalies in 3NF  |
| 4NF         | BCNF + No multi-valued dependencies              | Multi-valued dependency      |
| 5NF         | 4NF + No join dependency                         | Join anomalies               |

---

## 8. ACID Properties

ACID ensures **reliable database transactions** even in the event of errors, crashes, or concurrent access.

### 8.1 Atomicity
A transaction is **all-or-nothing**. Either all operations commit, or none do.

```sql
-- Bank Transfer: Alice sends $500 to Bob
BEGIN TRANSACTION;
    UPDATE Accounts SET Balance = Balance - 500 WHERE AccountID = 'Alice';
    UPDATE Accounts SET Balance = Balance + 500 WHERE AccountID = 'Bob';
COMMIT;
-- If the second UPDATE fails, the ROLLBACK ensures Alice's money is restored.
-- Without atomicity: Alice loses $500 and Bob never receives it!
```

### 8.2 Consistency
A transaction takes the DB from one **valid state** to another, respecting all rules/constraints.

```sql
-- Constraint: Balance >= 0
BEGIN TRANSACTION;
    UPDATE Accounts SET Balance = Balance - 10000 WHERE AccountID = 'Alice';
    -- If Alice's balance would go negative → CONSTRAINT VIOLATION → ROLLBACK
COMMIT;
```

### 8.3 Isolation
Concurrent transactions execute as if they were **serial** — intermediate states invisible to others.

```sql
-- T1: Transfer $500 from Alice to Bob
-- T2: Read Alice's balance (concurrently)
-- Without isolation: T2 might see Alice's balance AFTER deduction but BEFORE Bob's credit
-- With isolation (e.g., SERIALIZABLE): T2 sees either the old or new consistent state
```

### 8.4 Durability
Once a transaction **commits**, changes are **permanent** — even if the system crashes.

- Achieved via: **Write-Ahead Logging (WAL)**, redo logs, disk persistence.
- A committed transaction survives power failures, crashes.

### ACID Summary Table

| Property    | Keyword         | Mechanism                        | Violation Example                          |
|-------------|-----------------|----------------------------------|--------------------------------------------|
| Atomicity   | All or nothing  | ROLLBACK / COMMIT                | Money debited but not credited             |
| Consistency | Valid state     | Constraints, triggers            | Balance goes negative despite constraint   |
| Isolation   | Concurrency     | Locks, MVCC, isolation levels    | Dirty read of uncommitted data             |
| Durability  | Permanent       | WAL, redo logs, fsync            | Committed data lost after crash            |

---

## 9. Transaction Isolation Levels

Isolation levels define how transactions interact. Higher isolation = more protection but less concurrency.

### Concurrency Problems

| Problem           | Description                                                               |
|-------------------|---------------------------------------------------------------------------|
| **Dirty Read**    | Reading uncommitted data from another transaction                         |
| **Non-Repeatable Read** | Same row returns different values in same transaction               |
| **Phantom Read**  | New rows appear in repeated range queries within same transaction         |
| **Lost Update**   | Two transactions update same row; one overwrites the other's changes      |

### Isolation Levels Table

| Isolation Level     | Dirty Read | Non-Repeatable Read | Phantom Read | Performance |
|---------------------|------------|---------------------|--------------|-------------|
| **READ UNCOMMITTED**| Possible   | Possible            | Possible     | Highest     |
| **READ COMMITTED**  | Prevented  | Possible            | Possible     | High        |
| **REPEATABLE READ** | Prevented  | Prevented           | Possible     | Medium      |
| **SERIALIZABLE**    | Prevented  | Prevented           | Prevented    | Lowest      |

```sql
-- Set isolation level (MySQL/PostgreSQL)
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
BEGIN;
    SELECT * FROM Accounts WHERE AccountID = 'Alice';
    -- ... later in same transaction
    SELECT * FROM Accounts WHERE AccountID = 'Alice'; -- same result (repeatable)
COMMIT;
```

> **MySQL Default**: REPEATABLE READ | **PostgreSQL Default**: READ COMMITTED

---

## 10. Indexing

An index is a data structure that speeds up data retrieval at the cost of additional storage and write overhead.

### 10.1 Clustered vs Non-Clustered Index

| Feature                | Clustered Index                          | Non-Clustered Index                      |
|------------------------|------------------------------------------|------------------------------------------|
| Data Organization      | Table rows physically sorted by index    | Separate structure; points to rows       |
| Count per Table        | Only ONE                                 | Multiple allowed                         |
| Leaf Nodes Contain     | Actual data rows                         | Pointers (row locators) to data          |
| Speed                  | Faster for range queries                 | Faster for exact lookups                 |
| Example                | Primary Key (by default in MySQL InnoDB) | `CREATE INDEX idx ON emp(DeptID)`        |
| Storage Overhead       | No extra; data IS the index              | Extra space for index structure          |

### 10.2 B-Tree Index

Most common index type. A balanced tree where:
- All leaf nodes at the same level
- Internal nodes guide the search
- `O(log n)` search, insert, delete

```
B-Tree for Salary column:
                [50000]
              /         \
        [30000]          [70000, 90000]
       /       \        /    |    \
  [10k,20k] [35k,40k] [55k] [80k] [95k,100k]
```

### 10.3 Hash Index

Uses a hash function to map keys to buckets. `O(1)` exact lookups but:
- **Cannot** do range queries (`BETWEEN`, `>`, `<`)
- No ordering
- Best for equality checks (`=`, `IN`)

### 10.4 When to Use Indexes

**Use indexes on:**
- Primary keys (automatic)
- Foreign key columns (for JOIN performance)
- Columns frequently used in `WHERE`, `ORDER BY`, `GROUP BY`
- High-cardinality columns (many distinct values)

**Avoid indexes on:**
- Small tables (full scan is faster)
- Columns with very few distinct values (e.g., gender — only 2 values)
- Columns rarely used in queries
- Tables with frequent bulk INSERTs/UPDATEs

---

## 11. NoSQL vs SQL

| Feature              | SQL (Relational)                    | NoSQL                                  |
|----------------------|-------------------------------------|----------------------------------------|
| Schema               | Fixed schema (predefined)           | Dynamic schema (flexible)              |
| Data Model           | Tables (rows + columns)             | Documents, Key-Value, Graph, Column    |
| Query Language       | Structured SQL                      | Varies (MongoDB query API, etc.)       |
| ACID Compliance      | Full ACID                           | Often BASE (eventually consistent)     |
| Scalability          | Vertical (scale up)                 | Horizontal (scale out)                 |
| Joins                | Powerful JOIN support               | Joins are expensive/avoided            |
| Best For             | Complex queries, transactions       | High-volume, unstructured, flexible data|
| Examples             | MySQL, PostgreSQL, Oracle, SQL Server| MongoDB, Cassandra, Redis, DynamoDB    |
| Consistency          | Strong consistency                  | Eventual consistency (typical)         |

### NoSQL Database Types

| Type         | Description                              | Use Case                      | Example         |
|--------------|------------------------------------------|-------------------------------|-----------------|
| Document     | JSON-like documents                      | Content management, catalogs  | MongoDB         |
| Key-Value    | Simple key → value pairs                 | Caching, sessions             | Redis           |
| Column-Family| Columns grouped into families            | Time-series, IoT              | Cassandra, HBase|
| Graph        | Nodes and edges for relationships        | Social networks, routing      | Neo4j           |

---

## 12. CAP Theorem

**Brewer's CAP Theorem** states that a distributed data store can guarantee at most **two** of the following three properties simultaneously:

```
         Consistency (C)
              /\
             /  \
            /    \
           /      \
          /________\
Availability (A)  Partition Tolerance (P)
```

| Property                  | Definition                                                              |
|---------------------------|-------------------------------------------------------------------------|
| **Consistency (C)**       | Every read receives the most recent write (all nodes see same data)    |
| **Availability (A)**      | Every request gets a (non-error) response — but not necessarily latest |
| **Partition Tolerance (P)**| System continues despite network partitions (message loss)            |

> **In reality**: Network partitions are unavoidable in distributed systems, so **P is always required**.
> Therefore, real systems choose between **CP** or **AP**:

| System Type | Trade-off         | Examples                            |
|-------------|------------------|-------------------------------------|
| **CP**      | C + P (no A)     | MongoDB (strong consistency mode), HBase, Zookeeper |
| **AP**      | A + P (no C)     | Cassandra, DynamoDB, CouchDB        |
| **CA**      | C + A (no P)     | Traditional RDBMS (single-node)     |

### BASE vs ACID

NoSQL systems often follow **BASE** instead of ACID:
- **B**asically **A**vailable: System guarantees availability
- **S**oft state: State may change over time (even without input)
- **E**ventually consistent: System will become consistent over time

---

## 13. 20 Important SQL Queries

> **Schema Used Throughout:**
> - `Employees(EmpID, Name, Salary, DeptID, ManagerID, HireDate)`
> - `Departments(DeptID, DeptName)`

---

### Q1. Find the 2nd Highest Salary

```sql
-- Method 1: Using LIMIT/OFFSET
SELECT DISTINCT Salary
FROM Employees
ORDER BY Salary DESC
LIMIT 1 OFFSET 1;

-- Method 2: Using subquery (works across all SQL dialects)
SELECT MAX(Salary) AS SecondHighest
FROM Employees
WHERE Salary < (SELECT MAX(Salary) FROM Employees);

-- Method 3: Using DENSE_RANK (handles ties correctly)
SELECT Salary AS SecondHighest
FROM (
    SELECT Salary, DENSE_RANK() OVER (ORDER BY Salary DESC) AS rnk
    FROM Employees
) ranked
WHERE rnk = 2
LIMIT 1;
```

---

### Q2. Find Department with Maximum Number of Employees

```sql
SELECT d.DeptName, COUNT(e.EmpID) AS EmployeeCount
FROM Employees e
JOIN Departments d ON e.DeptID = d.DeptID
GROUP BY e.DeptID, d.DeptName
ORDER BY EmployeeCount DESC
LIMIT 1;

-- If multiple departments share the max count, return all:
SELECT d.DeptName, COUNT(e.EmpID) AS EmployeeCount
FROM Employees e
JOIN Departments d ON e.DeptID = d.DeptID
GROUP BY e.DeptID, d.DeptName
HAVING COUNT(e.EmpID) = (
    SELECT MAX(cnt) FROM (
        SELECT COUNT(EmpID) AS cnt FROM Employees GROUP BY DeptID
    ) sub
);
```

---

### Q3. Find Employees Without Managers (Top-Level)

```sql
-- Method 1: NULL check
SELECT EmpID, Name FROM Employees WHERE ManagerID IS NULL;

-- Method 2: NOT EXISTS
SELECT e.EmpID, e.Name
FROM Employees e
WHERE NOT EXISTS (
    SELECT 1 FROM Employees m WHERE m.EmpID = e.ManagerID
);
```

---

### Q4. Find Duplicate Records (by Name)

```sql
-- Find names that appear more than once
SELECT Name, COUNT(*) AS Occurrences
FROM Employees
GROUP BY Name
HAVING COUNT(*) > 1;

-- Show full duplicate rows
SELECT *
FROM Employees
WHERE Name IN (
    SELECT Name FROM Employees GROUP BY Name HAVING COUNT(*) > 1
)
ORDER BY Name;

-- Delete duplicates, keep lowest EmpID
DELETE FROM Employees
WHERE EmpID NOT IN (
    SELECT MIN(EmpID) FROM Employees GROUP BY Name
);
```

---

### Q5. Calculate Running Total of Salary

```sql
SELECT
    EmpID,
    Name,
    HireDate,
    Salary,
    SUM(Salary) OVER (ORDER BY HireDate
                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS RunningTotal
FROM Employees
ORDER BY HireDate;
```

---

### Q6. Find Employees Earning More Than Their Department Average

```sql
SELECT e.Name, e.Salary, e.DeptID,
       dept_avg.AvgSalary
FROM Employees e
JOIN (
    SELECT DeptID, AVG(Salary) AS AvgSalary
    FROM Employees
    GROUP BY DeptID
) dept_avg ON e.DeptID = dept_avg.DeptID
WHERE e.Salary > dept_avg.AvgSalary;
```

---

### Q7. Find the Nth Highest Salary (Generalized)

```sql
-- Replace N with desired rank (e.g., N=3 for 3rd highest)
SELECT DISTINCT Salary
FROM Employees
ORDER BY Salary DESC
LIMIT 1 OFFSET N-1;  -- e.g., OFFSET 2 for 3rd highest

-- Using DENSE_RANK for any N:
SELECT Salary FROM (
    SELECT Salary, DENSE_RANK() OVER (ORDER BY Salary DESC) AS rnk
    FROM Employees
) ranked
WHERE rnk = N;
```

---

### Q8. Find Employees Hired in the Last 30 Days

```sql
SELECT * FROM Employees
WHERE HireDate >= CURDATE() - INTERVAL 30 DAY;

-- PostgreSQL:
WHERE HireDate >= CURRENT_DATE - INTERVAL '30 days';
```

---

### Q9. Pivot — Count Employees Per Department (Horizontal)

```sql
SELECT
    SUM(CASE WHEN d.DeptName = 'Engineering' THEN 1 ELSE 0 END) AS Engineering,
    SUM(CASE WHEN d.DeptName = 'Marketing'   THEN 1 ELSE 0 END) AS Marketing,
    SUM(CASE WHEN d.DeptName = 'HR'          THEN 1 ELSE 0 END) AS HR
FROM Employees e
JOIN Departments d ON e.DeptID = d.DeptID;
```

---

### Q10. Find Manager of Each Employee (Self JOIN)

```sql
SELECT
    e.Name       AS Employee,
    m.Name       AS Manager,
    e.Salary     AS EmployeeSalary
FROM Employees e
LEFT JOIN Employees m ON e.ManagerID = m.EmpID;
```

---

### Q11. Rank Employees Within Each Department by Salary

```sql
SELECT
    e.Name,
    d.DeptName,
    e.Salary,
    RANK() OVER (PARTITION BY e.DeptID ORDER BY e.Salary DESC) AS SalaryRank
FROM Employees e
JOIN Departments d ON e.DeptID = d.DeptID;
```

---

### Q12. Find Employees with Same Salary

```sql
SELECT DISTINCT e1.Name, e1.Salary
FROM Employees e1
JOIN Employees e2 ON e1.Salary = e2.Salary AND e1.EmpID <> e2.EmpID
ORDER BY e1.Salary;
```

---

### Q13. Cumulative Salary Percentage Per Department

```sql
SELECT
    e.Name, e.DeptID, e.Salary,
    ROUND(
        100.0 * SUM(e.Salary) OVER (PARTITION BY e.DeptID ORDER BY e.Salary) /
        SUM(e.Salary) OVER (PARTITION BY e.DeptID),
        2
    ) AS CumulativePct
FROM Employees e;
```

---

### Q14. Find Departments with No Employees

```sql
-- Method 1: LEFT JOIN + NULL check
SELECT d.DeptName
FROM Departments d
LEFT JOIN Employees e ON d.DeptID = e.DeptID
WHERE e.EmpID IS NULL;

-- Method 2: NOT EXISTS
SELECT DeptName FROM Departments d
WHERE NOT EXISTS (
    SELECT 1 FROM Employees e WHERE e.DeptID = d.DeptID
);
```

---

### Q15. Year-over-Year Salary Growth (LAG)

```sql
SELECT
    EmpID, Name,
    YEAR(HireDate) AS Year,
    Salary,
    LAG(Salary) OVER (PARTITION BY EmpID ORDER BY YEAR(HireDate)) AS PrevSalary,
    ROUND(100.0 * (Salary - LAG(Salary) OVER (PARTITION BY EmpID ORDER BY YEAR(HireDate)))
          / LAG(Salary) OVER (PARTITION BY EmpID ORDER BY YEAR(HireDate)), 2) AS GrowthPct
FROM Employees;
```

---

### Q16. Find Employees Whose Name Starts with 'A' and Ends with 'e'

```sql
SELECT * FROM Employees
WHERE Name LIKE 'A%e';
-- 'A%' = starts with A, '%e' = ends with e
-- Combined: starts with A AND ends with e
```

---

### Q17. Find Top 3 Earners in Each Department

```sql
SELECT Name, DeptID, Salary
FROM (
    SELECT Name, DeptID, Salary,
           DENSE_RANK() OVER (PARTITION BY DeptID ORDER BY Salary DESC) AS rnk
    FROM Employees
) ranked
WHERE rnk <= 3;
```

---

### Q18. Find Employees Whose Salary is Above Company Average

```sql
SELECT Name, Salary
FROM Employees
WHERE Salary > (SELECT AVG(Salary) FROM Employees)
ORDER BY Salary DESC;
```

---

### Q19. Find the Median Salary

```sql
-- MySQL
SELECT AVG(Salary) AS MedianSalary
FROM (
    SELECT Salary,
           ROW_NUMBER() OVER (ORDER BY Salary)                          AS rn,
           COUNT(*) OVER ()                                              AS total
    FROM Employees
) sub
WHERE rn IN (FLOOR((total + 1) / 2), CEIL((total + 1) / 2));

-- PostgreSQL
SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY Salary) AS MedianSalary
FROM Employees;
```

---

### Q20. Delete All Rows Except the Latest Record Per Employee

```sql
-- Keep only the most recent hire record per employee name
DELETE FROM Employees
WHERE EmpID NOT IN (
    SELECT MAX(EmpID)
    FROM Employees
    GROUP BY Name
);

-- Safer method using CTE (PostgreSQL):
WITH latest AS (
    SELECT MAX(EmpID) AS MaxID FROM Employees GROUP BY Name
)
DELETE FROM Employees
WHERE EmpID NOT IN (SELECT MaxID FROM latest);
```

---

### Bonus SQL Quick Reference

```sql
-- CASE WHEN (conditional logic)
SELECT Name,
    CASE
        WHEN Salary >= 100000 THEN 'High'
        WHEN Salary >= 60000  THEN 'Medium'
        ELSE 'Low'
    END AS SalaryBand
FROM Employees;

-- COALESCE (return first non-NULL value)
SELECT Name, COALESCE(ManagerID, 0) AS ManagerID FROM Employees;

-- EXISTS vs IN
-- EXISTS is faster when subquery returns large result sets
SELECT Name FROM Employees e
WHERE EXISTS (SELECT 1 FROM Departments d WHERE d.DeptID = e.DeptID AND d.DeptName = 'Engineering');

-- UNION vs UNION ALL
-- UNION removes duplicates; UNION ALL keeps all rows (faster)
SELECT Name FROM Employees
UNION ALL
SELECT Name FROM ArchivedEmployees;

-- String Functions
SELECT UPPER(Name), LOWER(Name), LENGTH(Name),
       SUBSTRING(Name, 1, 5), CONCAT(Name, ' - ', DeptID)
FROM Employees;

-- Date Functions
SELECT DATEDIFF(CURDATE(), HireDate) AS DaysWorked,
       YEAR(HireDate) AS HireYear,
       MONTHNAME(HireDate) AS HireMonth
FROM Employees;
```

---

*End of DBMS Knowledge Base — PlaceMentor AI*
