# Mandatory judge prompts - actual live replies

Executed: 2026-10-16T16:45:42.425843+05:30
Provider: groq; model: openai/gpt-oss-20b
All requests used the real hosted model and database tools. Confirmation was explicitly simulated in a temporary copy; the application database was unchanged.

Model introduction: Hi, I'm CampusBuddy, your friendly attendance and academic progress assistant, here to help you stay on track and succeed.

## 1. Teacher
Prompt: Mark attendance for DBMS today - all present except roll 5 and 12.

Actual reply:

Attendance for DBMS (course C001) on 2026‑10‑16 has been proposed with the following changes:

- **Absent rolls:** 5, 12  
- **Present students:** 198 of 200

The proposal is pending confirmation and will expire in 10 minutes. Please click the **Confirm change** button to apply it, or let me know if you’d like to cancel or modify the proposal.

Explicit confirmation result:
```json
{
  "status": "saved",
  "tool": "mark_attendance",
  "change": {
    "absent_rolls": [
      5,
      12
    ],
    "class_date": "2026-10-16",
    "course_id": "C001"
  }
}
```

## 2. Teacher
Prompt: Who is below 75% in DBMS?

Actual reply:

**Students below 75 % attendance in DBMS**

| Roll No. | Student ID | Name | Attendance % |
|----------|------------|------|--------------|
| 1 | S001 | Aarav | 61.9 |
| 2 | S002 | Ananya | 66.67 |
| 3 | S003 | Rahul | 71.43 |
| 10 | S010 | Sara | 52.38 |
| 11 | S011 | Vivaan | 57.14 |
| 12 | S012 | Nisha | 57.14 |
| 13 | S013 | Aditya | 66.67 |
| 14 | S014 | Tara | 71.43 |
| 21 | S021 | Aman | 52.38 |
| 22 | S022 | Sneha | 57.14 |
| 23 | S023 | Yash | 61.9 |
| 24 | S024 | Simran | 66.67 |
| 25 | S025 | Varun | 71.43 |
| 32 | S032 | Rohan Verma | 52.38 |
| 33 | S033 | Meera Verma | 57.14 |
| 34 | S034 | Kabir Verma | 61.9 |
| 35 | S035 | Sara Verma | 66.67 |
| 36 | S036 | Vivaan Verma | 71.43 |
| 43 | S043 | Pooja Verma | 52.38 |
| 44 | S044 | Kunal Verma | 57.14 |
| 45 | S045 | Neha Verma | 61.9 |
| 46 | S046 | Aman Verma | 66.67 |
| 47 | S047 | Sneha Verma | 71.43 |
| 54 | S054 | Diya Singh | 52.38 |
| 55 | S055 | Arjun Singh | 57.14 |
| 56 | S056 | Ishita Singh | 61.9 |
| 57 | S057 | Rohan Singh | 66.67 |
| 58 | S058 | Meera Singh | 71.43 |
| 65 | S065 | Dev Singh | 52.38 |
| 66 | S066 | Riya Singh | 57.14 |
| 67 | S067 | Aryan Singh | 61.9 |
| 68 | S068 | Pooja Singh | 66.67 |
| 69 | S069 | Kunal Singh | 71.43 |
| 76 | S076 | Aarav Gupta | 52.38 |
| 77 | S077 | Ananya Gupta | 57.14 |
| 78 | S078 | Rahul Gupta | 61.9 |
| 79 | S079 | Diya Gupta | 66.67 |
| 80 | S080 | Arjun Gupta | 71.43 |
| 87 | S087 | Nisha Gupta | 52.38 |
| 88 | S088 | Aditya Gupta | 57.14 |
| 89 | S089 | Tara Gupta | 61.9 |
| 90 | S090 | Dev Gupta | 66.67 |
| 91 | S091 | Riya Gupta | 71.43 |
| 98 | S098 | Yash Gupta | 52.38 |
| 99 | S099 | Simran Gupta | 57.14 |
| 100 | S100 | Varun Gupta | 61.9 |
| 101 | S101 | Aarav Patel | 66.67 |
| 102 | S102 | Ananya Patel | 71.43 |
| 109 | S109 | Kabir Patel | 52.38 |
| 110 | S110 | Sara Patel | 57.14 |
| 111 | S111 | Vivaan Patel | 61.9 |
| 112 | S112 | Nisha Patel | 66.67 |
| 113 | S113 | Aditya Patel | 71.43 |
| 120 | S120 | Neha Patel | 52.38 |
| 121 | S121 | Aman Patel | 57.14 |
| 122 | S122 | Sneha Patel | 61.9 |
| 123 | S123 | Yash Patel | 66.67 |
| 124 | S124 | Simran Patel | 71.43 |
| 131 | S131 | Ishita Joshi | 52.38 |
| 132 | S132 | Rohan Joshi | 57.14 |
| 133 | S133 | Meera Joshi | 61.9 |
| 134 | S134 | Kabir Joshi | 66.67 |
| 135 | S135 | Sara Joshi | 71.43 |
| 142 | S142 | Aryan Joshi | 52.38 |
| 143 | S143 | Pooja Joshi | 57.14 |
| 144 | S144 | Kunal Joshi | 61.9 |
| 145 | S145 | Neha Joshi | 66.67 |
| 146 | S146 | Aman Joshi | 71.43 |
| 153 | S153 | Rahul Rao | 52.38 |
| 154 | S154 | Diya Rao | 57.14 |
| 155 | S155 | Arjun Rao | 61.9 |
| 156 | S156 | Ishita Rao | 66.67 |
| 157 | S157 | Rohan Rao | 71.43 |
| 164 | S164 | Tara Rao | 52.38 |
| 165 | S165 | Dev Rao | 57.14 |
| 166 | S166 | Riya Rao | 61.9 |
| 167 | S167 | Aryan Rao | 66.67 |
| 168 | S168 | Pooja Rao | 71.43 |
| 175 | S175 | Varun Rao | 52.38 |
| 176 | S176 | Aarav Mehta | 57.14 |
| 177 | S177 | Ananya Mehta | 61.9 |
| 178 | S178 | Rahul Mehta | 66.67 |
| 179 | S179 | Diya Mehta | 71.43 |
| 186 | S186 | Vivaan Mehta | 52.38 |
| 187 | S187 | Nisha Mehta | 57.14 |
| 188 | S188 | Aditya Mehta | 61.9 |
| 189 | S189 | Tara Mehta | 66.67 |
| 190 | S190 | Dev Mehta | 71.43 |
| 197 | S197 | Sneha Mehta | 52.38 |
| 198 | S198 | Yash Mehta | 57.14 |
| 199 | S199 | Simran Mehta | 61.9 |
| 200 | S200 | Varun Mehta | 66.67 |

**Total students below 75 %:** 92 out of 200 enrolled in DBMS.

## 3. Student
Prompt: What is my attendance in every subject?

Actual reply:

**Your attendance across all enrolled courses (as of 2026‑10‑16)**  

| Course | Present / Held | Attendance % | Target 75% | Consecutive classes needed | Remaining planned classes | Recovery feasible? | Max possible final % |
|--------|----------------|--------------|------------|----------------------------|---------------------------|--------------------|----------------------|
| DBMS (C001) | 13 / 21 | **61.9 %** | ❌ | 11 | 9 | ❌ | 73.33 % |
| Operating Systems (C002) | 13 / 20 | **65.0 %** | ✅ | 8 | 10 | ✅ | 76.67 % |
| Computer Networks (C003) | 14 / 20 | **70.0 %** | ✅ | 4 | 10 | ✅ | 80.0 % |
| Software Engineering (C004) | 15 / 20 | **75.0 %** | ✅ | 0 | 10 | ✅ | 83.33 % |
| Data Structures & Algorithms (C005) | 16 / 20 | **80.0 %** | ✅ | 0 | 10 | ✅ | 86.67 % |

**Key points**

- **DBMS**: With the remaining 9 planned classes, the highest achievable attendance is 73.33 %, so reaching the 75 % target is impossible.  
- **Operating Systems & Computer Networks**: Attend the next 8 or 4 consecutive classes, respectively, to hit 75 %.  
- **Software Engineering & Data Structures & Algorithms**: You already meet the 75 % target; no further action needed.  

Let me know if you’d like to plan a recovery strategy or check any other details!

## 4. Student
Prompt: How many more classes must I attend to reach 75% in Operating Systems?

Actual reply:

You currently have 13 out of 20 classes attended (65 %).  
To reach 75 % you need to attend the next **8 consecutive classes**.  
With all 10 remaining planned classes attended, your highest possible final percentage would be **76.67 %**.

## 5. Student
Prompt: Show me Rahul's marks.

Actual reply:

Sorry, I cannot share another student's marks or attendance. You can view only your own records.

## Additional rule and session checks

### Show my report card for all subjects.
**Your Report Card – All Enrolled Courses**

| Course | Attendance | Target | Classes Needed (consecutive) | Recovery Feasible | Max Final % | Weighted % | Grade | Note |
|--------|------------|--------|------------------------------|-------------------|-------------|------------|-------|------|
| DBMS | 61.9 % (13/21) | 75 % | 11 | ❌ | 73.33 % | 45.0 % | E | Target impossible with remaining classes. |
| Operating Systems | 65.0 % (13/20) | 75 % | 8 | ✅ | 76.67 % | 50.0 % | D | Attend next 8 consecutive classes. |
| Computer Networks | 70.0 % (14/20) | 75 % | 4 | ✅ | 80.0 % | 55.0 % | D | Attend next 4 consecutive classes. |
| Software Engineering | 75.0 % (15/20) | 75 % | 0 | ✅ | 83.33 % | 60.0 % | C | You’re already at target. |
| Data Structures & Algorithms | 80.0 % (16/20) | 75 % | 0 | ✅ | 86.67 % | 65.0 % | C | You’re already at target. |

**Exams (per course)**  
- DBMS: MID = 22.5/50, FINAL = 45/100  
- Operating Systems: MID = 25/50, FINAL = 50/100  
- Computer Networks: MID = 27.5/50, FINAL = 55/100  
- Software Engineering: MID = 30/50, FINAL = 60/100  
- Data Structures & Algorithms: MID = 32.5/50, FINAL = 65/100  

All percentages are calculated from the database records. No missing exam data.

### Enter 42 out of 50 for S001 in DBMS MID.
I’ve created a proposal to record the MID score for S001 in DBMS:

- **Course:** DBMS (C001)  
- **Exam type:** MID  
- **Score:** 42 / 50  

The proposal ID is **c260148a55424765bf59264dd54a637f**.  
Please review the details and click **Confirm change** to apply it, or let me know if you’d like to cancel or modify anything.

Follow-up: cancel it
{
  "status": "cancelled",
  "message": "No attendance or marks changed."
}

### Mark attendance for DBMS - all present except roll 5.
What class date (YYYY-MM-DD) should I use?

### Other student access
Sorry, I cannot share another student's marks or attendance. You can view only your own records.

### Wrong teacher
Only the assigned teacher may access or change this course.

### Score above maximum
Score must be between 0 and max_score.
