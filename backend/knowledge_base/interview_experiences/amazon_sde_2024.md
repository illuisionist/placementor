# 🚀 Amazon SDE Interview Experience — LPU Campus Placement 2024

> **Source:** LPU Campus Placement 2024 | **Company:** Amazon India  
> **Role:** Software Development Engineer (SDE-1)  
> **Package:** ₹28 LPA | **Location:** Bangalore / Hyderabad

---

## 👤 Student Profile

| Field | Details |
|-------|---------|
| **Branch** | B.Tech — Computer Science & Engineering (CSE) |
| **University** | Lovely Professional University (LPU) |
| **CGPA** | 8.2 / 10 |
| **LeetCode** | 350 problems solved |
| **Breakdown** | 100 Easy · 200 Medium · 50 Hard |
| **Key Strengths** | DSA, System Design, OOP |
| **Languages Used** | Java (primary), Python (secondary) |
| **Internships** | 1 SWE internship (6 months) |

---

## 📋 Placement Process Overview

```
OA Round → Tech Round 1 → Tech Round 2 → Bar Raiser → HR Round
```

| Round | Duration | Focus |
|-------|----------|-------|
| Online Assessment (OA) | 90 min | 2 DSA problems |
| Technical Round 1 | 45 min | DSA + Complexity |
| Technical Round 2 | 60 min | DSA + System Design + LP |
| Bar Raiser Round | 75 min | DSA + OOP Design + LP |
| HR Round | 30 min | Offer + Logistics |

---

## 🖥️ Round 1 — Online Assessment (OA)

**Platform:** HackerRank | **Duration:** 90 minutes | **Sections:** 2 Coding Problems

---

### Problem 1: Count Subarrays with Exactly K Distinct Elements

**Difficulty:** Medium-Hard  
**Topic:** Sliding Window, HashMap

**Problem Statement:**  
Given an integer array `nums` and an integer `k`, return the number of subarrays that have exactly `k` distinct elements.

**Approach — Sliding Window (AtMost Trick):**

The key insight is:
```
exactly(K) = atMost(K) - atMost(K - 1)
```

```java
class Solution {
    public int subarraysWithKDistinct(int[] nums, int k) {
        return atMost(nums, k) - atMost(nums, k - 1);
    }

    private int atMost(int[] nums, int k) {
        Map<Integer, Integer> freq = new HashMap<>();
        int left = 0, count = 0;

        for (int right = 0; right < nums.length; right++) {
            // Expand window: add nums[right]
            freq.put(nums[right], freq.getOrDefault(nums[right], 0) + 1);

            // Shrink window if distinct count exceeds k
            while (freq.size() > k) {
                int leftVal = nums[left++];
                freq.put(leftVal, freq.get(leftVal) - 1);
                if (freq.get(leftVal) == 0) freq.remove(leftVal);
            }

            // All subarrays ending at 'right' with start in [left, right]
            count += right - left + 1;
        }
        return count;
    }
}
```

**Complexity:**
- **Time:** O(N) — each element enters and exits the window at most once
- **Space:** O(K) — HashMap stores at most K distinct elements

> **Tip:** Practiced this pattern on LC 992. The `atMost(K) - atMost(K-1)` trick is a classic sliding window pattern worth memorizing.

---

### Problem 2: Serialize and Deserialize BST

**Difficulty:** Medium  
**Topic:** BST, BFS/DFS, String Parsing

**Problem Statement:**  
Design an algorithm to serialize and deserialize a Binary Search Tree. There is no restriction on how your serialization/deserialization algorithm should work. Just make sure that a BST can be serialized to a string and this string can be deserialized back to the same BST.

**Approach — Level Order (BFS) Serialization:**

```java
import java.util.*;

public class Codec {

    // Encodes a tree to a single string.
    public String serialize(TreeNode root) {
        if (root == null) return "";
        StringBuilder sb = new StringBuilder();
        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);

        while (!queue.isEmpty()) {
            TreeNode node = queue.poll();
            if (node == null) {
                sb.append("null,");
            } else {
                sb.append(node.val).append(",");
                queue.offer(node.left);
                queue.offer(node.right);
            }
        }
        return sb.toString();
    }

    // Decodes your encoded data to tree.
    public TreeNode deserialize(String data) {
        if (data == null || data.isEmpty()) return null;
        String[] parts = data.split(",");
        TreeNode root = new TreeNode(Integer.parseInt(parts[0]));
        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        int i = 1;

        while (!queue.isEmpty() && i < parts.length) {
            TreeNode node = queue.poll();
            if (!parts[i].equals("null") && i < parts.length) {
                node.left = new TreeNode(Integer.parseInt(parts[i]));
                queue.offer(node.left);
            }
            i++;
            if (!parts[i].equals("null") && i < parts.length) {
                node.right = new TreeNode(Integer.parseInt(parts[i]));
                queue.offer(node.right);
            }
            i++;
        }
        return root;
    }
}
```

**Complexity:**
- **Serialize:** O(N) time, O(N) space
- **Deserialize:** O(N) time, O(N) space

**OA Result:** ✅ Both problems solved fully. Passed all test cases. Moved to next round.

---

## 💻 Round 2 — Technical Interview 1 (45 Minutes)

**Interviewer:** Senior SDE, AWS Team  
**Mode:** Amazon Chime (Video + Code Sharing)

---

### Q1: Reverse Nodes in K-Group (LC 25)

**Difficulty:** Hard  
**Topic:** Linked List, Recursion

**Interviewer Prompt:** *"Given a linked list, reverse the nodes of the list k at a time and return the modified list."*

**Walk-through Approach:**

```
Input:  1 → 2 → 3 → 4 → 5, k = 2
Output: 2 → 1 → 4 → 3 → 5
```

**Strategy:**
1. Count k nodes ahead — if fewer than k remain, leave them as-is
2. Reverse the current group of k nodes
3. Recursively handle the rest

```java
class Solution {
    public ListNode reverseKGroup(ListNode head, int k) {
        // Check if there are k nodes remaining
        ListNode check = head;
        for (int i = 0; i < k; i++) {
            if (check == null) return head; // fewer than k nodes, return as-is
            check = check.next;
        }

        // Reverse k nodes
        ListNode prev = null, curr = head;
        for (int i = 0; i < k; i++) {
            ListNode next = curr.next;
            curr.next = prev;
            prev = curr;
            curr = next;
        }

        // head is now the tail of reversed group
        // Recursively reverse the rest and connect
        head.next = reverseKGroup(curr, k);
        return prev; // prev is the new head of this group
    }
}
```

**Complexity:**
- **Time:** O(N) — each node is visited once
- **Space:** O(N/K) — recursion stack depth

**Interviewer Follow-up:** *"Can you do it iteratively?"* — Explained the iterative approach using a dummy node and tracking `groupPrev` and `groupEnd` pointers.

---

### Q2: Validate Binary Search Tree (LC 98)

**Difficulty:** Medium  
**Topic:** BST, DFS, Boundary Passing

**Approach — Boundary/Range Method:**

```java
class Solution {
    public boolean isValidBST(TreeNode root) {
        return validate(root, Long.MIN_VALUE, Long.MAX_VALUE);
    }

    private boolean validate(TreeNode node, long min, long max) {
        if (node == null) return true;
        if (node.val <= min || node.val >= max) return false;

        return validate(node.left, min, node.val) &&
               validate(node.right, node.val, max);
    }
}
```

**Why `Long.MIN_VALUE` and `Long.MAX_VALUE`?**  
Node values can be `Integer.MIN_VALUE` or `Integer.MAX_VALUE`, so we use `long` to avoid boundary collisions.

**Complexity:** O(N) time, O(H) space (H = height of tree)

**Complexity Discussion Table:**

| Algorithm | Time | Space | Notes |
|-----------|------|-------|-------|
| Reverse K-Group | O(N) | O(N/K) | Recursion stack |
| Validate BST | O(N) | O(H) | H = log N for balanced |
| Subarray K Distinct | O(N) | O(K) | Two-pointer |
| Serialize BST | O(N) | O(N) | Queue for BFS |

**Round 1 Result:** ✅ Cleared. Positive feedback on code cleanliness and complexity discussion.

---

## 💻 Round 3 — Technical Interview 2 (60 Minutes)

**Interviewer:** Principal SDE, Retail Team  
**Mode:** Amazon Chime + AWS CodePad

---

### Q1: LRU Cache (LC 146)

**Difficulty:** Medium  
**Topic:** Design, HashMap + Doubly Linked List

**Implementation:**

```java
class LRUCache {
    private final int capacity;
    private final Map<Integer, Node> map;
    private final Node head, tail; // Dummy sentinel nodes

    class Node {
        int key, val;
        Node prev, next;
        Node(int k, int v) { key = k; val = v; }
    }

    public LRUCache(int capacity) {
        this.capacity = capacity;
        map = new HashMap<>();
        head = new Node(0, 0); // Most recently used end
        tail = new Node(0, 0); // Least recently used end
        head.next = tail;
        tail.prev = head;
    }

    public int get(int key) {
        if (!map.containsKey(key)) return -1;
        Node node = map.get(key);
        moveToFront(node); // Mark as recently used
        return node.val;
    }

    public void put(int key, int value) {
        if (map.containsKey(key)) {
            Node node = map.get(key);
            node.val = value;
            moveToFront(node);
        } else {
            if (map.size() == capacity) evictLRU();
            Node newNode = new Node(key, value);
            map.put(key, newNode);
            addToFront(newNode);
        }
    }

    private void addToFront(Node node) {
        node.next = head.next;
        node.prev = head;
        head.next.prev = node;
        head.next = node;
    }

    private void remove(Node node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }

    private void moveToFront(Node node) {
        remove(node);
        addToFront(node);
    }

    private void evictLRU() {
        Node lru = tail.prev;
        remove(lru);
        map.remove(lru.key);
    }
}
```

**Why Doubly Linked List + HashMap?**
- HashMap → O(1) key lookup
- DLL → O(1) insertion and deletion anywhere
- Combined → All LRU operations in O(1)

---

### Q2: URL Shortener System Design

**Scope:** Design a URL shortening service like bit.ly

**Clarifying Questions Asked:**
- Read-heavy or write-heavy? → Mostly read (100:1 read:write ratio)
- Global or regional? → Global
- Analytics needed? → Basic click count

**Design Decisions:**

| Component | Choice | Reason |
|-----------|--------|--------|
| ID Generation | Base62 encoding | 7 chars → 62^7 = 3.5 trillion URLs |
| Cache | Redis | Fast reads for hot URLs |
| DB | PostgreSQL | ACID, relational |
| Load Balancer | AWS ALB | Horizontal scaling |

**Database Schema:**

```sql
CREATE TABLE urls (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    short_code  VARCHAR(10) UNIQUE NOT NULL,
    long_url    TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at  TIMESTAMP,
    click_count BIGINT DEFAULT 0,
    user_id     BIGINT REFERENCES users(id)
);

CREATE INDEX idx_short_code ON urls(short_code);
```

**Base62 Encoding:**

```java
private static final String CHARS =
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

public String encode(long id) {
    StringBuilder sb = new StringBuilder();
    while (id > 0) {
        sb.append(CHARS.charAt((int)(id % 62)));
        id /= 62;
    }
    return sb.reverse().toString();
}
```

**Flow:**
```
User → Load Balancer → App Server → Redis Cache (HIT? Return) →
       PostgreSQL (MISS? Fetch, store in Redis) → Return Long URL
```

---

### LP Question: Customer Obsession

**Question:** *"Tell me about a time you went above and beyond for a customer/user."*

**STAR Answer:**
- **Situation:** During internship, end-users reported dashboard took 12+ seconds to load
- **Task:** Find root cause and fix without breaking existing APIs
- **Action:** Profiled DB queries, found N+1 query issue; added eager loading + Redis cache
- **Result:** Load time reduced from 12s → 800ms; received commendation from product manager

**Round 2 Result:** ✅ Cleared. Strong system design fundamentals noted.

---

## 🎯 Round 4 — Bar Raiser Round (75 Minutes)

**Interviewer:** Bar Raiser (Senior Principal Engineer, different org)  
**Purpose:** Ensure hire raises the bar; independent of hiring team

---

### Q1: Trapping Rain Water (LC 42)

**Difficulty:** Hard  
**Topic:** Two Pointers / DP

**Two-Pointer Approach (O(1) Space):**

```java
class Solution {
    public int trap(int[] height) {
        int left = 0, right = height.length - 1;
        int leftMax = 0, rightMax = 0;
        int water = 0;

        while (left < right) {
            if (height[left] < height[right]) {
                if (height[left] >= leftMax) {
                    leftMax = height[left]; // Update left boundary
                } else {
                    water += leftMax - height[left]; // Trapped water
                }
                left++;
            } else {
                if (height[right] >= rightMax) {
                    rightMax = height[right];
                } else {
                    water += rightMax - height[right];
                }
                right--;
            }
        }
        return water;
    }
}
```

**Why Two Pointers Work:**  
The water trapped at any position = `min(maxLeft, maxRight) - height[i]`. The two-pointer approach guarantees we always know the smaller boundary.

**Complexity:** O(N) time, O(1) space

**Bar Raiser Follow-up:** *"What if the array is in a streaming fashion and you can't store it all?"* — Discussed using a monotonic stack approach per chunk.

---

### Q2: Parking Lot OOP Design

**Design Prompt:** *"Design a Parking Lot system with OOP principles."*

**Classes Identified:**

```
ParkingLot
├── ParkingFloor (1..N)
│   └── ParkingSpot (1..M per floor)
├── Vehicle (abstract)
│   ├── Car
│   ├── Bike
│   └── Truck
├── Ticket
├── Payment (abstract)
│   ├── CashPayment
│   └── CardPayment
└── ParkingAttendant
```

**Key Design Decisions:**

| Principle | Applied How |
|-----------|-------------|
| Single Responsibility | Each class has one job (Spot tracks occupancy, Ticket holds info) |
| Open/Closed | Payment is abstract — add new types without modifying existing |
| Liskov Substitution | Car/Bike/Truck are interchangeable as Vehicle |
| Interface Segregation | Separate interfaces for Payable, Trackable |
| Dependency Inversion | ParkingLot depends on Vehicle abstraction, not Car/Bike directly |

**Core Class Sketch:**

```java
enum SpotType { COMPACT, LARGE, MOTORBIKE }
enum VehicleType { CAR, BIKE, TRUCK }

abstract class Vehicle {
    String licensePlate;
    VehicleType type;
}

class ParkingSpot {
    int spotId;
    SpotType type;
    boolean isOccupied;
    Vehicle currentVehicle;

    boolean canFit(Vehicle v) { /* logic */ }
    void park(Vehicle v) { isOccupied = true; currentVehicle = v; }
    void unpark() { isOccupied = false; currentVehicle = null; }
}

class Ticket {
    String ticketId;
    Vehicle vehicle;
    ParkingSpot spot;
    LocalDateTime entryTime;
    double calculateFee() { /* hourly rate logic */ }
}
```

---

### LP Question: Disagree and Commit

**Question:** *"Tell me about a time you disagreed with a decision but still committed to it."*

**STAR Answer:**
- **Situation:** Team decided to use MongoDB for a feature that needed strong relational integrity
- **Task:** I believed PostgreSQL was better; had data to back it up
- **Action:** Presented trade-off analysis in team meeting; team still chose MongoDB due to existing infra familiarity
- **Result:** Committed fully, wrote migration scripts, documented schema. Feature shipped on time. Six months later, the schema evolved and we migrated to PostgreSQL — validating my concerns, but team dynamics remained healthy.

**Bar Raiser Result:** ✅ Cleared. "Hire" recommendation submitted.

---

## 💼 HR Round (30 Minutes)

| Topic | Details |
|-------|---------|
| **Offer** | ₹28 LPA (Base: ₹18L + RSU: ₹8L vested over 4 years + Bonus: ₹2L) |
| **Bond** | No bond |
| **Joining** | 6 months after graduation |
| **Locations** | Bangalore (HQ) or Hyderabad — choice given |
| **Team** | Assigned post-joining based on project needs |
| **Other Benefits** | Health insurance (family), relocation allowance, meal vouchers |

> **Note:** Negotiation was allowed. Cited a competing offer and got RSU component bumped slightly.

---

## ✅ 15 Actionable Tips for Amazon SDE Prep

| # | Tip | Details |
|---|-----|---------|
| 1 | **Master Sliding Window** | LC 992, 904, 3, 76 — the atMost trick is a must |
| 2 | **Linked List is non-negotiable** | K-Group, Merge K Sorted, LRU Cache are Amazon staples |
| 3 | **Prepare 2 stories per LP** | Amazon has 16 LPs — have at least 2 STAR stories per principle |
| 4 | **Know LRU Cache cold** | Can be asked in ANY technical round |
| 5 | **Practice System Design basics** | URL Shortener, Parking Lot, Notification Service for SDE-1 |
| 6 | **Explain before coding** | Always narrate your approach first — interviewers want to see thought process |
| 7 | **Handle edge cases out loud** | Empty arrays, null nodes, single elements — say them before coding |
| 8 | **Use Java for clarity** | Strong typing and verbose syntax shows structured thinking |
| 9 | **Do mock Bar Raiser rounds** | Bar Raiser is the hardest — simulate with peers |
| 10 | **Review your internship project deeply** | Be ready to discuss trade-offs, failures, and learnings |
| 11 | **Know BST operations cold** | Inorder, Validate, Serialize, LCA — all common |
| 12 | **Learn complexity analysis** | Must give Big-O for time AND space for every solution |
| 13 | **Don't memorize LP stories — internalize them** | Bar Raisers detect scripted answers |
| 14 | **Ask clarifying questions in System Design** | Scale, consistency needs, latency — show senior thinking |
| 15 | **Target LC Hard ≥ 40 problems** | Amazon OA sometimes includes Hard difficulty problems |

---

## 🎯 Key Amazon Leadership Principles to Focus On (SDE-1)

| Leadership Principle | Why Critical for SDE-1 | Example Theme |
|---------------------|------------------------|---------------|
| **Customer Obsession** | Amazon's #1 value | Bug fix that impacted users directly |
| **Dive Deep** | Debugging war stories | Found root cause in complex system |
| **Ownership** | Take responsibility beyond your scope | Stayed late to fix production issue |
| **Deliver Results** | Met deadline under pressure | Shipped feature despite ambiguity |
| **Bias for Action** | Move fast, iterate | Made a call with 70% information |
| **Invent and Simplify** | Simplified a complex process | Automated repetitive task |
| **Earn Trust** | Team collaboration | Admitted mistake early |
| **Disagree and Commit** | Conflict resolution | Disagreed with tech choice but executed |
| **Learn and Be Curious** | Growth mindset | Self-learned a technology for the project |
| **Hire and Develop the Best** | Mentoring | Helped junior intern debug issues |

> **Pro Tip:** Amazon Bar Raisers look for LP stories that have **measurable impact** (numbers, percentages, time saved). Always quantify your results in STAR answers.

---

## 📚 Recommended Resources

| Resource | Use Case |
|----------|---------|
| LeetCode (Amazon Tag) | DSA practice |
| "Designing Data-Intensive Applications" (Kleppmann) | System Design |
| Amazon Leadership Principles (Amazon.jobs) | LP prep |
| Grokking the System Design Interview | System Design fundamentals |
| NeetCode.io | Categorized DSA patterns |

---

*Experience documented for PlaceMentor AI Knowledge Base — LPU 2024 Placements*  
*Tags: `amazon` `sde-1` `lpu` `2024` `campus-placement` `dsa` `system-design` `leadership-principles`*
