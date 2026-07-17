# Operating Systems — Comprehensive Interview Guide
> **PlaceMentor AI Knowledge Base** | Core Subjects | OS
> Covers: Processes, Threads, Scheduling, Synchronization, Deadlock, Memory Management, Virtual Memory

---

## Table of Contents
1. [Process vs Thread](#1-process-vs-thread)
2. [Process States & PCB](#2-process-states--pcb)
3. [CPU Scheduling Algorithms](#3-cpu-scheduling-algorithms)
4. [Synchronization](#4-synchronization)
5. [Deadlock](#5-deadlock)
6. [Memory Management](#6-memory-management)
7. [Virtual Memory & Page Replacement](#7-virtual-memory--page-replacement)
8. [Thrashing](#8-thrashing)
9. [Interview Q&A — 20 Questions](#9-interview-qa--20-questions)

---

## 1. Process vs Thread

### Definitions
- **Process**: An independent program in execution with its own memory space, resources, and state.
- **Thread**: A lightweight unit of execution within a process; shares memory with sibling threads.

### Comparison Table

| Feature                  | Process                              | Thread                              |
|--------------------------|--------------------------------------|-------------------------------------|
| Definition               | Program in execution                 | Smallest unit of CPU execution       |
| Memory Space             | Separate address space               | Shared address space (within process)|
| Communication (IPC)      | Expensive (pipes, sockets, shared mem)| Easy & fast (shared globals/heap)    |
| Context Switch Cost      | High                                 | Low                                 |
| Creation Overhead        | High (`fork()`)                      | Low (`pthread_create()`)            |
| Crash Impact             | Isolated — doesn't affect others     | One thread crash can kill process    |
| Synchronization Needed?  | Between processes via IPC            | Yes — race conditions on shared data |
| Resource Ownership       | Owns: code, data, heap, files, etc.  | Shares code, data, heap; own stack  |
| Scheduling Unit          | Yes                                  | Yes (in most modern OSes)           |
| Example                  | Chrome process, VS Code process      | Tab renderer, JS engine in Chrome   |

### Types of Threads
- **User-Level Threads (ULT)**: Managed by user library; OS unaware. Fast context switch but blocked on I/O blocks entire process.
- **Kernel-Level Threads (KLT)**: Managed by OS kernel. More overhead but true parallelism.
- **Hybrid**: Combination of ULT and KLT (e.g., Solaris).

---

## 2. Process States & PCB

### Process State Diagram (Text-Based)

```
          admit
  NEW ─────────────► READY ◄──────────────────────────────────┐
                       │                                        │
               dispatch│                                        │ I/O complete /
            (scheduler)│                                        │ event occurs
                       ▼                                        │
                   RUNNING ──── preempted ──────────────────────┘
                    │   │
          exit/     │   │ waiting for
        terminate   │   │ I/O or event
                    │   ▼
                TERMINATED  WAITING/BLOCKED
                              │
                              │ I/O complete
                              ▼
                           READY
```

### Process States Explained

| State       | Description                                                              |
|-------------|--------------------------------------------------------------------------|
| **New**     | Process is being created                                                 |
| **Ready**   | Process is in memory, waiting for CPU                                    |
| **Running** | Process is currently executing on CPU                                    |
| **Waiting** | Process waiting for I/O or event (not using CPU)                         |
| **Terminated**| Process finished execution; resources being released                   |

> **Suspended States** (some OSes): Ready-Suspended, Blocked-Suspended — process swapped out to disk.

### Process Control Block (PCB)

The PCB (also called Task Control Block) is the data structure the OS maintains for each process.

```
┌────────────────────────────────────────────┐
│              PROCESS CONTROL BLOCK          │
├────────────────────────────────────────────┤
│  Process ID (PID)         │  e.g., 1042    │
│  Process State            │  Ready/Running │
│  Program Counter (PC)     │  Next instr.   │
│  CPU Registers            │  AX, BX, SP…  │
│  CPU Scheduling Info      │  Priority, ptr │
│  Memory Management Info   │  Page tables   │
│  Accounting Info          │  CPU time used │
│  I/O Status Info          │  Open files    │
│  Parent PID (PPID)        │  e.g., 1000    │
│  List of Open Files       │  FD table      │
└────────────────────────────────────────────┘
```

### Context Switch
When the OS switches CPU from one process/thread to another:
1. Save current process state → PCB
2. Load next process state ← PCB
3. Resume execution

> **Context switch is pure overhead** — no useful work done during the switch itself.

---

## 3. CPU Scheduling Algorithms

### Key Metrics
- **Arrival Time (AT)**: When process arrives in ready queue
- **Burst Time (BT)**: CPU time required
- **Completion Time (CT)**: When process finishes
- **Turnaround Time (TAT)** = CT − AT
- **Waiting Time (WT)** = TAT − BT
- **Response Time**: Time from arrival to first CPU execution

---

### 3.1 FCFS — First Come First Serve

- **Non-preemptive**. Processes served in arrival order.
- **Problem**: Convoy effect — short jobs stuck behind long ones.

**Example:**

| Process | AT | BT |
|---------|----|----|
| P1      | 0  | 4  |
| P2      | 1  | 3  |
| P3      | 2  | 1  |

```
Gantt Chart:
|  P1  |  P2  | P3 |
0      4      7    8

TAT: P1=4, P2=6, P3=6   Avg TAT = 5.33
WT:  P1=0, P2=3, P3=5   Avg WT  = 2.67
```

---

### 3.2 SJF — Shortest Job First (Non-Preemptive)

- Selects process with **shortest burst time** when CPU is free.
- **Optimal** for minimizing average waiting time (among non-preemptive).

**Example (same processes):**

```
At t=0: Only P1 available → run P1
At t=4: P2(BT=3), P3(BT=1) → pick P3
At t=5: P2 runs

Gantt Chart:
|  P1  | P3 | P2  |
0      4    5     8

TAT: P1=4, P2=7, P3=3   Avg TAT = 4.67
WT:  P1=0, P2=4, P3=2   Avg WT  = 2.00
```

---

### 3.3 SRTF — Shortest Remaining Time First (Preemptive SJF)

- Preemptive version of SJF. If a new process arrives with shorter remaining burst, preempt current.

**Example:**

| Process | AT | BT |
|---------|----|----|
| P1      | 0  | 8  |
| P2      | 1  | 4  |
| P3      | 2  | 2  |
| P4      | 3  | 1  |

```
t=0: P1 starts (only one), rem=8
t=1: P2 arrives (BT=4 < rem P1=7) → preempt, P2 runs
t=2: P3 arrives (BT=2 < rem P2=3) → preempt, P3 runs
t=3: P4 arrives (BT=1 < rem P3=1)? No (equal), P3 continues
t=4: P3 done, P4(1) < P2(3) < P1(7) → P4 runs
t=5: P4 done, P2 runs (rem=3)
t=8: P2 done, P1 runs (rem=7)
t=15: P1 done

Gantt Chart:
|P1|  P2 |  P3  |P4|   P2   |         P1          |
0  1     2      4  5        8                      15
```

---

### 3.4 Round Robin (RR)

- **Preemptive**. Each process gets a fixed **time quantum (Q)**.
- After Q expires, process is preempted and added to end of ready queue.
- **Best for time-sharing systems**.

**Example (Q=2):**

| Process | AT | BT |
|---------|----|----|
| P1      | 0  | 5  |
| P2      | 0  | 3  |
| P3      | 0  | 4  |

```
Gantt Chart (Q=2):
|P1|P2|P3|P1|P2|P3|P1|
0  2  4  6  8  9 11 12

TAT: P1=12, P2=9, P3=11   Avg TAT = 10.67
WT:  P1=7,  P2=6, P3=7    Avg WT  = 6.67
```

> **Tip**: Smaller Q → more responsive but more context switches. Larger Q → behaves like FCFS.

---

### 3.5 Priority Scheduling

- Each process has a priority. Higher priority → scheduled first.
- Can be **preemptive** or **non-preemptive**.
- **Problem**: Starvation — low priority processes may never run.
- **Solution**: Aging — gradually increase priority of waiting processes.

**Example (Non-Preemptive, lower number = higher priority):**

| Process | AT | BT | Priority |
|---------|----|----|----------|
| P1      | 0  | 4  | 3        |
| P2      | 0  | 2  | 1        |
| P3      | 0  | 3  | 2        |

```
Gantt Chart:
| P2 | P3  |  P1  |
0    2     5      9

TAT: P2=2, P3=5, P1=9   Avg TAT = 5.33
WT:  P2=0, P3=2, P1=5   Avg WT  = 2.33
```

### Algorithm Comparison Summary

| Algorithm | Preemptive | Optimal? | Starvation | Overhead |
|-----------|-----------|----------|------------|----------|
| FCFS      | No        | No       | No         | Low      |
| SJF       | No        | Yes (avg WT)| No      | Medium   |
| SRTF      | Yes       | Yes (avg WT)| Yes     | High     |
| Round Robin| Yes      | No       | No         | Medium   |
| Priority  | Both      | No       | Yes        | Medium   |
| MLFQ      | Yes       | Approx.  | No (aging) | High     |

---

## 4. Synchronization

### The Critical Section Problem
A **critical section** is a code segment that accesses shared resources. Requirements for a solution:
1. **Mutual Exclusion**: Only one process in critical section at a time.
2. **Progress**: If no process is in CS, a waiting process must be able to enter.
3. **Bounded Waiting**: A process must not wait forever (no starvation).

---

### 4.1 Mutex (Mutual Exclusion Lock)

A binary lock — either locked or unlocked.

```c
// Pseudocode
mutex lock;

// Thread A
mutex_lock(&lock);
  // Critical Section
  shared_counter++;
mutex_unlock(&lock);

// Thread B
mutex_lock(&lock);    // blocks if A holds lock
  shared_counter--;
mutex_unlock(&lock);
```

- **Ownership**: Only the thread that locked can unlock it.
- **Use case**: Protecting shared data structures.

---

### 4.2 Semaphore

A variable with two atomic operations:
- **wait(S)** / P(S): `S--; if S < 0, block;`
- **signal(S)** / V(S): `S++; if S <= 0, wake a blocked process;`

```c
// Binary Semaphore (acts like mutex)
semaphore S = 1;

// Process A
wait(S);      // S becomes 0
  // Critical Section
signal(S);    // S becomes 1

// Counting Semaphore — e.g., limit 3 concurrent DB connections
semaphore connections = 3;

connect_to_db() {
    wait(connections);    // decrement; blocks if 0
    // use connection
    close_connection();
    signal(connections);  // increment
}
```

**Semaphore vs Mutex:**

| Feature         | Mutex                     | Semaphore                       |
|-----------------|---------------------------|---------------------------------|
| Value           | Binary (0/1)              | Integer (0 to N)                |
| Ownership       | Yes — locker must unlock  | No — any process can signal     |
| Use Case        | Mutual exclusion          | Signaling + counting resources  |
| Deadlock risk   | Yes (if used carelessly)  | Yes                             |

---

### 4.3 Monitors

A high-level synchronization construct — a class/module with:
- Shared variables
- Procedures (only one active at a time — mutual exclusion automatic)
- **Condition variables** (`wait()` and `signal()`)

```java
// Monitor example in Java using synchronized
class BoundedBuffer {
    private int[] buffer;
    private int count = 0, in = 0, out = 0;

    public synchronized void produce(int item) throws InterruptedException {
        while (count == buffer.length) wait(); // buffer full
        buffer[in] = item;
        in = (in + 1) % buffer.length;
        count++;
        notifyAll();
    }

    public synchronized int consume() throws InterruptedException {
        while (count == 0) wait(); // buffer empty
        int item = buffer[out];
        out = (out + 1) % buffer.length;
        count--;
        notifyAll();
        return item;
    }
}
```

### Classic Synchronization Problems

| Problem                   | Description                                         | Solution                    |
|---------------------------|-----------------------------------------------------|-----------------------------|
| Producer-Consumer         | Producer fills buffer; consumer empties it          | Semaphores: empty, full, mutex |
| Readers-Writers           | Multiple readers OR one writer at a time            | Reader/writer semaphores    |
| Dining Philosophers       | 5 philosophers, 5 forks — avoid deadlock & starvation | Asymmetric solution, monitors |

---

## 5. Deadlock

### Definition
A set of processes is **deadlocked** when each process is waiting for a resource held by another process in the set — circular wait with no progress.

### 5.1 Four Necessary Conditions (Coffman Conditions)

All four must hold simultaneously for deadlock:

| Condition            | Description                                                    |
|----------------------|----------------------------------------------------------------|
| **Mutual Exclusion** | At least one resource is non-sharable                         |
| **Hold and Wait**    | Process holding resources can request more                    |
| **No Preemption**    | Resources can't be forcibly taken from a process              |
| **Circular Wait**    | P1→R1→P2→R2→P1 — circular chain of waits                     |

### 5.2 Deadlock Prevention

Break at least one of the four conditions:

| Condition to Break   | Method                                                        |
|----------------------|---------------------------------------------------------------|
| Mutual Exclusion     | Use sharable resources (read-only files)                     |
| Hold and Wait        | Request all resources at once before starting                 |
| No Preemption        | Allow OS to preempt resources forcibly                        |
| Circular Wait        | Impose total ordering on resource types                       |

### 5.3 Deadlock Avoidance — Banker's Algorithm

**Concept**: Before granting a resource, check if system remains in a **safe state** (exists a sequence in which all processes can complete).

**Key Data Structures:**
- `Available[j]` — currently available instances of resource j
- `Max[i][j]` — max demand of process i for resource j
- `Allocation[i][j]` — currently allocated to process i
- `Need[i][j]` = Max[i][j] − Allocation[i][j]

**Example (5 processes, 3 resource types A, B, C):**

```
Allocation    Max         Available
           A  B  C     A  B  C     A  B  C
P0         0  1  0     7  5  3     3  3  2
P1         2  0  0     3  2  2
P2         3  0  2     9  0  2
P3         2  1  1     2  2  2
P4         0  0  2     4  3  3

Need = Max - Allocation
P0: 7 4 3
P1: 1 2 2
P2: 6 0 0
P3: 0 1 1
P4: 4 3 1

Safety Check (Available = 3 3 2):
Step 1: P1 needs (1,2,2) ≤ (3,3,2)? YES → run P1, free (2,0,0) → Available=(5,3,2)
Step 2: P3 needs (0,1,1) ≤ (5,3,2)? YES → run P3, free (2,1,1) → Available=(7,4,3)
Step 3: P4 needs (4,3,1) ≤ (7,4,3)? YES → run P4, free (0,0,2) → Available=(7,4,5)
Step 4: P0 needs (7,4,3) ≤ (7,4,5)? YES → run P0, free (0,1,0) → Available=(7,5,5)
Step 5: P2 needs (6,0,0) ≤ (7,5,5)? YES → run P2

Safe Sequence: P1 → P3 → P4 → P0 → P2  ✓ SAFE STATE
```

### 5.4 Deadlock Detection & Recovery

- **Detection**: Resource Allocation Graph (RAG) — cycle = deadlock (single instance resources)
- **Recovery Options**:
  - **Process Termination**: Kill all deadlocked processes, or kill one at a time.
  - **Resource Preemption**: Forcibly take resource from a process.

---

## 6. Memory Management

### 6.1 Paging

Divides:
- **Physical Memory** → fixed-size **frames**
- **Logical Memory** → fixed-size **pages** (same size as frames)

**Address Translation:**
```
Logical Address  →  [ Page Number | Page Offset ]
                         ↓
                     Page Table
                         ↓
Physical Address →  [ Frame Number | Page Offset ]
```

**Formula:**
```
Page Size = 2^n bytes  (n = offset bits)
Page Number = Logical Address / Page Size
Page Offset = Logical Address mod Page Size
Physical Address = Frame_Number × Page_Size + Page_Offset
```

**Example:**
```
Page Size = 4 KB = 4096 bytes = 2^12
Logical Address = 12500

Page Number = 12500 / 4096 = 3  (page 3)
Page Offset = 12500 mod 4096 = 212

If Page Table: Page 3 → Frame 7
Physical Address = 7 × 4096 + 212 = 28672 + 212 = 28884
```

**Advantages of Paging:**
- No external fragmentation
- Easy to implement

**Disadvantage:**
- Internal fragmentation (last page may not be full)
- Page table itself consumes memory (solved by multi-level paging or TLB)

### TLB (Translation Lookaside Buffer)

Fast cache for page table entries. On every memory access:
1. Check TLB → **TLB Hit**: direct frame number (fast)
2. TLB Miss → access page table in memory (slower)

**Effective Access Time (EAT):**
```
EAT = α × (TLB_time + Memory_time) + (1 - α) × (TLB_time + 2 × Memory_time)
where α = hit ratio
```

---

### 6.2 Segmentation

Divides memory into **variable-size segments** based on logical units (code, stack, heap, data).

```
Logical Address = <Segment Number, Offset>

Segment Table Entry:
  Base  — starting physical address
  Limit — length of segment

Physical Address = Base[Segment] + Offset
(valid only if Offset < Limit)
```

| Feature             | Paging                      | Segmentation                      |
|---------------------|-----------------------------|-----------------------------------|
| Division Unit       | Fixed-size pages            | Variable-size segments            |
| Fragmentation       | Internal                    | External                          |
| Programmer Visible? | No                          | Yes (code, data, stack segments)  |
| Sharing             | Page-level                  | Segment-level (easier)            |

---

## 7. Virtual Memory & Page Replacement

### Virtual Memory Concept
- Allows processes to use more memory than physically available.
- Pages not currently needed remain on **disk (swap space)**.
- On access to non-resident page → **Page Fault** → OS loads page from disk.

### Page Fault Handling
1. Reference to page not in memory → Page Fault trap
2. OS finds the page on disk
3. If free frame exists → load page; else → run **page replacement algorithm**
4. Update page table, restart instruction

---

### Page Replacement Algorithms

**Reference String**: 7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2
**Number of Frames**: 3

---

#### 7.1 FIFO (First-In First-Out)

Replace the **oldest** page.

```
Ref:    7   0   1   2   0   3   0   4   2   3   0   3   2
Frames:
F1:     7   7   7   2   2   2   2   4   4   4   0   0   0
F2:     -   0   0   0   0   3   3   3   2   2   2   2   2
F3:     -   -   1   1   1   1   0   0   0   3   3   3   3

Fault:  ✗   ✗   ✗   ✗   -   ✗   ✗   ✗   ✗   ✗   ✗   -   -

Total Page Faults = 9
```

> **Belady's Anomaly**: Increasing frames can INCREASE page faults in FIFO!

---

#### 7.2 LRU (Least Recently Used)

Replace the page that was **used least recently**.

```
Ref:    7   0   1   2   0   3   0   4   2   3   0   3   2
Frames:
F1:     7   7   7   2   2   2   2   4   4   3   0   0   2
F2:     -   0   0   0   0   0   0   0   2   2   2   2   2
F3:     -   -   1   1   1   3   3   3   3   3   3   3   3

Fault:  ✗   ✗   ✗   ✗   -   ✗   -   ✗   -   ✗   ✗   -   ✗

Total Page Faults = 8
```

---

#### 7.3 Optimal (OPT / Belady's Optimal)

Replace the page that will **not be used for the longest time** in future. (Theoretical — requires future knowledge.)

```
Ref:    7   0   1   2   0   3   0   4   2   3   0   3   2
Frames:
F1:     7   7   7   2   2   2   2   2   2   2   2   2   2
F2:     -   0   0   0   0   0   0   4   4   3   3   3   3
F3:     -   -   1   1   1   3   3   3   3   3   0   0   0

Fault:  ✗   ✗   ✗   ✗   -   ✗   -   ✗   -   -   ✗   -   -

Total Page Faults = 7  ← Minimum possible
```

### Algorithm Comparison

| Algorithm | Page Faults (3 frames) | Suffers Belady's Anomaly? | Practical? |
|-----------|------------------------|---------------------------|------------|
| FIFO      | 9                      | Yes                       | Yes        |
| LRU       | 8                      | No                        | Yes (approx.) |
| Optimal   | 7                      | No                        | No (theoretical) |

---

## 8. Thrashing

### Definition
**Thrashing** occurs when a process spends more time **paging (swapping pages in/out)** than executing useful work.

### Cause
- Too many processes in memory → each gets too few frames.
- Processes constantly page fault → CPU utilization drops.
- OS sees low CPU utilization → brings in MORE processes → worsens paging.

```
         CPU Utilization
              ▲
          100%│          ●
              │        ●   ●
              │      ●       ●
              │    ●           ●  ← THRASHING begins
              │  ●               ●
              └──────────────────────► Degree of Multiprogramming
```

### Solutions
1. **Working Set Model**: Track pages used in last Δ time window (working set). Ensure enough frames for working set.
2. **Page Fault Frequency (PFF)**: Monitor fault rate. Too high → give more frames. Too low → reclaim frames.
3. **Reduce Degree of Multiprogramming**: Swap out some processes entirely.
4. **Increase Physical RAM**.

---

## 9. Interview Q&A — 20 Questions

### Q1. What is the difference between a process and a thread?
**A:** A process is an independent program with its own memory space, while a thread is a lightweight unit of execution within a process that shares the process's memory. Threads are faster to create and switch between, but share resources making synchronization necessary.

---

### Q2. What are the five process states?
**A:** New, Ready, Running, Waiting/Blocked, Terminated. A process moves from New→Ready→Running. It can move to Waiting on I/O and back to Ready when I/O completes. It moves to Terminated when done.

---

### Q3. What is a PCB and what does it contain?
**A:** Process Control Block is the OS's data structure for a process. It contains: PID, process state, program counter, CPU registers, scheduling info (priority), memory management info (page tables), I/O status (open files), and accounting info (CPU time used).

---

### Q4. Which scheduling algorithm gives minimum average waiting time?
**A:** **SJF (Shortest Job First)** is provably optimal for minimizing average waiting time among non-preemptive algorithms. Its preemptive version SRTF is optimal overall but requires knowledge of burst times.

---

### Q5. What is the convoy effect in FCFS?
**A:** Convoy effect happens when short processes are stuck behind a long process. The long process "convoys" others, increasing average waiting time significantly. This is FCFS's main disadvantage.

---

### Q6. What is starvation and how is it solved?
**A:** Starvation is when a low-priority process never gets CPU time because higher-priority processes keep arriving. Solution: **Aging** — gradually increase the priority of waiting processes over time.

---

### Q7. What is the difference between mutex and semaphore?
**A:** A mutex is a binary lock with ownership (only the locker can unlock). A semaphore is an integer variable with no ownership — any process can signal it. Semaphores can be counting (value > 1) for managing multiple resource instances.

---

### Q8. What are the four conditions for deadlock?
**A:** Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait. All four must hold simultaneously. Breaking any one prevents deadlock.

---

### Q9. How does Banker's algorithm avoid deadlock?
**A:** Before granting a resource request, Banker's algorithm simulates the allocation and checks if the system remains in a **safe state** (i.e., there exists a safe sequence where all processes can eventually complete). If safe, grant; else, make the process wait.

---

### Q10. What is the difference between paging and segmentation?
**A:** Paging divides memory into fixed-size pages/frames — no external fragmentation but has internal fragmentation. Segmentation divides memory into variable-size logical segments (code, data, stack) — has external fragmentation but matches programmer's view.

---

### Q11. What is a TLB and how does it help?
**A:** Translation Lookaside Buffer is a fast cache for page table entries. Instead of two memory accesses per reference (page table + data), TLB gives the frame number in one fast lookup on a hit, reducing average memory access time significantly.

---

### Q12. What is a page fault?
**A:** A page fault occurs when a process accesses a page not currently in physical memory. The OS handles it by: saving state, finding the page on disk, loading it into a free frame (possibly evicting another page), updating the page table, and restarting the instruction.

---

### Q13. Why is Optimal page replacement not used in practice?
**A:** Optimal requires future knowledge of which pages will be referenced — impossible in a real system. It's used only as a theoretical benchmark to compare other algorithms.

---

### Q14. What is Belady's Anomaly?
**A:** Belady's Anomaly is the counterintuitive phenomenon where increasing the number of frames causes **more** page faults in FIFO replacement. It does not occur with LRU or Optimal (stack algorithms).

---

### Q15. What is thrashing?
**A:** Thrashing is when a process spends more time swapping pages than executing. It happens when too many processes compete for too few frames. The working set model or page fault frequency approach can be used to detect and prevent thrashing.

---

### Q16. What is the difference between internal and external fragmentation?
**A:** **Internal fragmentation**: Allocated memory is larger than needed (e.g., paging — last page not full). **External fragmentation**: Total free memory is enough but not contiguous (e.g., segmentation, variable partition). Solution: **Compaction** for external fragmentation.

---

### Q17. What is a race condition? Give an example.
**A:** A race condition occurs when the output of a program depends on the non-deterministic ordering of thread executions. Example: Two threads both read `counter=5`, increment it, and write `6` — but the expected result is `7`. Solved with synchronization (mutex/semaphore).

---

### Q18. What is the difference between preemptive and non-preemptive scheduling?
**A:** In **preemptive** scheduling, the OS can forcibly take the CPU away from a running process (e.g., when time quantum expires or higher-priority process arrives). In **non-preemptive**, once a process starts running, it runs until it voluntarily gives up the CPU (I/O wait or exit).

---

### Q19. What is multiprogramming vs multitasking vs multiprocessing?
**A:**
- **Multiprogramming**: Multiple programs in memory; CPU switches on I/O to maximize CPU utilization.
- **Multitasking**: Time-sharing — CPU rapidly switches between processes giving illusion of simultaneity.
- **Multiprocessing**: Multiple CPUs executing processes truly in parallel.

---

### Q20. Explain the working set model.
**A:** The working set model tracks the set of pages a process has used in the last Δ time units (working set window). The OS ensures each process has enough frames to hold its working set. If total working set demand > available frames → suspend some processes to prevent thrashing.

---

*End of Operating Systems Knowledge Base — PlaceMentor AI*
