# Planning Document: Modern School Management System

This document outlines the development plan for the Modern School Management System. The goal is to create a simple, functional application based on the requirements in the PRD (v2.3), avoiding complex architectural overhead.

---

## Phase 0: Project Setup & Configuration

This phase focuses on preparing the development environment and initializing the project structure.

* **Step 1: Environment Setup**
    * Install necessary software: Python (for Django), Node.js (for Next.js), PostgreSQL, and Redis.
    * Set up virtual environments for both backend and frontend projects.

* **Step 2: Initialize Repositories**
    * Create a Git repository for the project.
    * Set up two main directories: `/backend` and `/frontend`.

* **Step 3: Backend Project Initialization**
    * [cite_start]Initialize a Django project in the `/backend` directory.
    * Install core dependencies: `Django`, `djangorestframework`, `psycopg2-binary`, `celery`, `redis`.
    * [cite_start]Configure `settings.py` for database connection to PostgreSQL  and basic project settings.

* **Step 4: Frontend Project Initialization**
    * [cite_start]Initialize a Next.js 15 project in the `/frontend` directory.
    * Install core dependencies: `tailwindcss`.
    * [cite_start]Set up Shadcn UI for component architecture.

---

## Phase 1: Backend Development (Django API)

This phase focuses on building the core logic, database models, and API endpoints.

* **Step 1: Database Models**
    * **User Models**: Create a custom User model inheriting from Django's base user to include roles (Super Admin, School Owner, Teacher, Student, Parent, Office Account).
    * **School Models**:
        * [cite_start]`School`: Fields for `name`, `address`, `contact_email`, `contact_number`, `logo`, `dashboard_primary_color`, `dashboard_secondary_color`, `smtp_settings`. Linked to a School Owner.
        * [cite_start]`SchoolGroup`: To group schools under one owner.
    * **Academic Models**:
        * `AcademicSession`, `Term`.
        * `Class` (e.g., Grade 5A).
        * `Subject`.
        * [cite_start]`TeacherAssignment`: Linking teachers to classes and subjects.
    * **Student Models**:
        * `Student`: Linked to a `School`, `Class`, and `Parent` user.
        * `Enrollment`.
    * **Financial Models**:
        * `FeeRecord`: To track student fees. Fields for `student`, `amount`, `status` (e.g., "Cleared", "Pending").
    * **Grading Models**:
        * `Result`: Linking `student`, `subject`, `term`. [cite_start]Fields for `first_ca`, `second_ca`, `exam_marks`.

* **Step 2: API Endpoints & Logic**
    * **Authentication**: Set up token-based authentication (e.g., JWT) for API access.
    * [cite_start]**Permissions**: Implement role-based permissions to restrict access based on user type (e.g., only Teachers can input grades, only owners can change school settings).
    * **Super Admin Endpoints (`/api/superadmin/`)**:
        * [cite_start]`POST /owners/`: Add a new School Owner.
        * [cite_start]`GET, PUT /owners/{id}/`: View/Edit a School Owner.
        * [cite_start]`GET, PUT /schools/{id}/`: View/Modify any school's records.
    * **School Owner Endpoints (`/api/owner/`)**:
        * [cite_start]`GET /dashboard/`: Fetch summary metrics for the owner's schools.
        * [cite_start]`PUT /schools/{id}/customize/`: Update school logo, colors, info.
        * [cite_start]`PUT /schools/{id}/smtp/`: Update SMTP settings.
        * [cite_start]`POST /users/manage`: Add teachers, students, office accounts.
        * [cite_start]`POST /academics/setup`: Define classes, subjects, terms.
    * **Teacher Endpoints (`/api/teacher/`)**:
        * [cite_start]`GET /dashboard/`: Get assigned classes.
        * [cite_start]`POST /grades/input/`: Endpoint to submit `1st CA`, `2nd CA`, and `Exam` marks for students in an assigned class.
    * **Student Endpoints (`/api/student/`)**:
        * [cite_start]`GET /profile/`: Fetch student's profile info.
        * [cite_start]`GET /results/`: Fetch termly results, but only if their fee status is "Cleared".
    * **Financials Endpoints (`/api/office/`)**:
        * `POST /fees/import`: Bulk import fee records.
        * `PUT /fees/student/{id}`: Update a student's fee status.
    * **API Documentation**: Generate Swagger (OpenAPI) documentation for all endpoints.

* **Step 3: Asynchronous Tasks**
    * [cite_start]Configure Celery and Redis.
    * [cite_start]Create a task to send an email to a parent when their child's results are generated. [cite_start]This task will use the school's specific SMTP settings.

---

## Phase 2: Frontend Development (Next.js)

This phase focuses on building the user interfaces for each role.

* **Step 1: Core UI & Layout**
    * Create a main layout component with a sidebar/navigation.
    * [cite_start]Develop a set of reusable UI components using **Shadcn UI/Tailwind CSS** (Buttons, Forms, Tables, Modals).
    * Implement login/logout functionality.

* **Step 2: Super Admin Dashboard**
    * [cite_start]Create a view to list all school owners and schools.
    * [cite_start]Build forms (in modals) to add/edit school owners.

* **Step 3: School Owner Dashboard**
    * [cite_start]**Main Dashboard**: Display key metrics.
    * [cite_start]**School Settings Page**: Build forms to upload a school logo, set the school name/address, and configure theme colors and SMTP settings.
    * [cite_start]**User Management Page**: Create tables to display teachers and students, with buttons to add new users.
    * [cite_start]**Academics Page**: Interface to define classes and subjects.
    * [cite_start]**Results Page**: View to see the `Class Result Summary` table for generated results.

* **Step 4: Teacher Dashboard**
    * [cite_start]**Main Dashboard**: Display a list of assigned classes.
    * **Grade Entry Page**:
        * Allow the teacher to select a class, subject, and term.
        * Display a table of students in that class.
        * [cite_start]Provide input fields for `1st CA`, `2nd CA`, and `Exam` marks for each student.

* **Step 5: Student Dashboard**
    * [cite_start]**Profile Page**: View profile information and update profile image.
    * **Results Page**:
        * [cite_start]Display the student's termly results in a table as specified in the PRD.
        * If fee status is not "Cleared", show a message indicating results are unavailable.
        * [cite_start]Include a "Download as PDF" button.

---

## Phase 3: Integration, Testing & Deployment

This final phase connects the backend and frontend, ensures functionality, and prepares for release.

* **Step 1: API Integration**
    * Connect the Next.js frontend components to the Django API endpoints.
    * Implement token handling on the frontend to manage user sessions.
    * Ensure data flows correctly between the two systems.

* **Step 2: Testing**
    * **Backend**: Write basic unit tests for critical logic (e.g., result calculation, fee status checks).
    * **Frontend**: Conduct manual user-flow testing for each user role.
        * Can a School Owner customize their school?
        * Can a Teacher input grades correctly?
        * Can a Student view and download their results (and are they blocked if fees are unpaid)?
        * Are emails sent upon result generation?
    * **Cross-browser Testing**: Perform quick checks on major browsers (Chrome, Firefox).

* **Step 3: Deployment (Simple)**
    * **Backend**: Deploy the Django application (e.g., using Gunicorn and Nginx on a cloud server).
    * **Frontend**: Deploy the Next.js application (e.g., using Vercel or as a static build served by Nginx).
    * **Database**: Set up a production PostgreSQL database instance.
    * **Final Configuration**: Ensure all environment variables (database URLs, secret keys) are correctly set in the production environment.

    API Endpoints Documentation
🔐 Authentication & User Management
POST   /api/auth/login/                    # User login
POST   /api/auth/token/refresh/            # Refresh JWT token
GET    /api/auth/profile/                  # Get current user profile
PUT    /api/auth/profile/                  # Update current user profile
POST   /api/auth/change-password/          # Change password

# User Management (Admin only)
GET    /api/auth/users/                    # List all users
POST   /api/auth/users/create/             # Create new user
GET    /api/auth/users/{id}/               # Get user details
PUT    /api/auth/users/{id}/               # Update user
DELETE /api/auth/users/{id}/               # Delete user

# Teacher CSV Import/Export
POST   /api/auth/teachers/import/csv/      # Import teachers from CSV
GET    /api/auth/teachers/export/csv/      # Export teachers to CSV
GET    /api/auth/teachers/template/csv/    # Download teacher CSV template
GET    /api/auth/teachers/import/status/{task_id}/  # Check import status
🏫 Schools Management
GET    /api/schools/                       # List schools
POST   /api/schools/                       # Create new school
GET    /api/schools/{id}/                  # Get school details
PUT    /api/schools/{id}/                  # Update school
DELETE /api/schools/{id}/                  # Delete school
GET    /api/schools/{id}/dashboard/        # Get school dashboard data
GET    /api/schools/dashboard/             # Get user dashboard (role-based)

# SMTP Settings
GET    /api/schools/{school_id}/smtp/      # Get SMTP settings
PUT    /api/schools/{school_id}/smtp/      # Update SMTP settings
POST   /api/schools/{school_id}/smtp/create/  # Create SMTP settings

# School Groups
GET    /api/schools/groups/                # List school groups
POST   /api/schools/groups/                # Create school group
GET    /api/schools/groups/{id}/           # Get school group details
PUT    /api/schools/groups/{id}/           # Update school group
DELETE /api/schools/groups/{id}/           # Delete school group
📚 Academic Management
# Academic Sessions
GET    /api/academics/sessions/            # List academic sessions
POST   /api/academics/sessions/            # Create academic session
GET    /api/academics/sessions/{id}/       # Get session details
PUT    /api/academics/sessions/{id}/       # Update session
DELETE /api/academics/sessions/{id}/       # Delete session

# Terms
GET    /api/academics/terms/               # List terms (filter: ?session={id})
POST   /api/academics/terms/               # Create term
GET    /api/academics/terms/{id}/          # Get term details
PUT    /api/academics/terms/{id}/          # Update term
DELETE /api/academics/terms/{id}/          # Delete term

# Subjects
GET    /api/academics/subjects/            # List subjects
POST   /api/academics/subjects/            # Create subject
GET    /api/academics/subjects/{id}/       # Get subject details
PUT    /api/academics/subjects/{id}/       # Update subject
DELETE /api/academics/subjects/{id}/       # Delete subject
POST   /api/academics/subjects/bulk-create/  # Bulk create subjects

# Classes
GET    /api/academics/classes/             # List classes (filter: ?session={id})
POST   /api/academics/classes/             # Create class
GET    /api/academics/classes/{id}/        # Get class details
PUT    /api/academics/classes/{id}/        # Update class
DELETE /api/academics/classes/{id}/        # Delete class
POST   /api/academics/classes/bulk-create/ # Bulk create classes

# Teacher Assignments
GET    /api/academics/assignments/         # List teacher assignments
POST   /api/academics/assignments/         # Create assignment
GET    /api/academics/assignments/{id}/    # Get assignment details
PUT    /api/academics/assignments/{id}/    # Update assignment
DELETE /api/academics/assignments/{id}/    # Delete assignment

# Teacher-specific
GET    /api/academics/teacher/assignments/ # Get logged-in teacher's assignments
GET    /api/academics/teacher/classes/     # Get teacher's assigned classes
👨‍🎓 Student Management
# Students
GET    /api/students/                      # List students (filter: ?class={id})
POST   /api/students/                      # Create student
GET    /api/students/{id}/                 # Get student details
PUT    /api/students/{id}/                 # Update student
DELETE /api/students/{id}/                 # Delete student
GET    /api/students/profile/              # Get logged-in student's profile
GET    /api/students/dashboard/            # Get student dashboard

# CSV Import/Export
POST   /api/students/import/csv/           # Import students from CSV
GET    /api/students/export/csv/           # Export students to CSV
GET    /api/students/template/csv/         # Download student CSV template
GET    /api/students/import/status/{task_id}/  # Check import status

# Enrollments
GET    /api/students/enrollments/          # List enrollments
POST   /api/students/enrollments/          # Create enrollment
GET    /api/students/enrollments/{id}/     # Get enrollment details
PUT    /api/students/enrollments/{id}/     # Update enrollment
DELETE /api/students/enrollments/{id}/     # Delete enrollment

# Attendance
GET    /api/students/attendance/           # List attendance (filters: ?date={date}&student={id}&class={id})
POST   /api/students/attendance/           # Record attendance
GET    /api/students/attendance/{id}/      # Get attendance details
PUT    /api/students/attendance/{id}/      # Update attendance
DELETE /api/students/attendance/{id}/      # Delete attendance
POST   /api/students/attendance/bulk/      # Bulk attendance recording
GET    /api/students/attendance/summary/   # Get attendance summary

# Class-specific
GET    /api/students/class/{class_id}/     # Get all students in a class
📊 Results Management
# Individual Results
GET    /api/results/                       # List results (filters: ?student={id}&term={id}&subject={id})
POST   /api/results/                       # Create result
GET    /api/results/{id}/                  # Get result details
PUT    /api/results/{id}/                  # Update result
DELETE /api/results/{id}/                  # Delete result

# Term Results
GET    /api/results/term-results/          # List term results
POST   /api/results/term-results/          # Create term result
GET    /api/results/term-results/{id}/     # Get term result details
PUT    /api/results/term-results/{id}/     # Update term result
DELETE /api/results/term-results/{id}/     # Delete term result

# Student-specific
GET    /api/results/student/my-results/    # Get logged-in student's results
GET    /api/results/student/term/{term_id}/ # Get student's specific term result

# Teacher-specific
POST   /api/results/teacher/bulk-input/    # Bulk input results for a class

# Admin Operations
POST   /api/results/generate/              # Generate term results
POST   /api/results/publish/               # Publish results

# Analytics
GET    /api/results/analytics/class-summary/      # Get class result summary
GET    /api/results/analytics/subject-performance/ # Get subject performance analysis

# Result Template
GET    /api/results/template/              # Get result template
PUT    /api/results/template/              # Update result template
GET    /api/results/template/{school_id}/  # Get school-specific template
💰 Financial Management
# Fee Structures
GET    /api/financials/fee-structures/     # List fee structures
POST   /api/financials/fee-structures/     # Create fee structure
GET    /api/financials/fee-structures/{id}/ # Get fee structure details
PUT    /api/financials/fee-structures/{id}/ # Update fee structure
DELETE /api/financials/fee-structures/{id}/ # Delete fee structure

# Fee Records
GET    /api/financials/fee-records/        # List fee records (filters: ?student={id}&term={id}&status={status})
POST   /api/financials/fee-records/        # Create fee record
GET    /api/financials/fee-records/{id}/   # Get fee record details
PUT    /api/financials/fee-records/{id}/   # Update fee record
DELETE /api/financials/fee-records/{id}/   # Delete fee record
POST   /api/financials/fee-records/generate/ # Generate fee records for students

# Fee CSV Import/Export
POST   /api/financials/fees/import/csv/    # Import fees from CSV
GET    /api/financials/fees/export/csv/    # Export fees to CSV
GET    /api/financials/fees/template/csv/  # Download fee CSV template
GET    /api/financials/fees/import/status/{task_id}/ # Check import status

# Payment Processing
POST   /api/financials/payments/bulk/      # Process bulk payments

# Student-specific
GET    /api/financials/student/fee-status/ # Get logged-in student's fee status

# Analytics
GET    /api/financials/analytics/          # Get fee analytics

# Invoices
GET    /api/financials/invoices/           # List invoices
POST   /api/financials/invoices/           # Create invoice
GET    /api/financials/invoices/{id}/      # Get invoice details
PUT    /api/financials/invoices/{id}/      # Update invoice
DELETE /api/financials/invoices/{id}/      # Delete invoice

# Discounts
GET    /api/financials/discount-schemes/   # List discount schemes
POST   /api/financials/discount-schemes/   # Create discount scheme
GET    /api/financials/student-discounts/  # List student discounts
POST   /api/financials/student-discounts/  # Apply discount to student
📖 API Documentation
GET    /api/schema/                        # OpenAPI schema
GET    /api/docs/                          # Swagger UI documentation
