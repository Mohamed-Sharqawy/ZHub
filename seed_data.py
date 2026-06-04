import os
import random
from datetime import datetime, timedelta, date

from faker import Faker

from website import create_app
from website.extensions import db
from website.models import (
    User, Student, Instructor, Course, Group, Enrollment,
    Attendance, Transaction, Certificate, StudentPerformance, CourseRating, InstructorRating, CourseSchedule,
    StudentProject, ProjectMedia, InstructorNote, Assignment, AssignmentSubmission, TrainerEvaluation
)

# Configuration
NUM_ADMINS = 2
NUM_INSTRUCTORS = 20
NUM_STUDENTS = 500
NUM_COURSES = 30
MAX_GROUPS_PER_COURSE = 5
MAX_ENROLLMENTS_PER_STUDENT = 4

fake = Faker()
Faker.seed(42)
random.seed(42)

app = create_app()

def clear_db():
    print("Clearing database...")
    # Delete in correct order to respect FK constraints
    Certificate.query.delete()
    Transaction.query.delete()
    Attendance.query.delete()
    StudentPerformance.query.delete()
    CourseRating.query.delete()
    InstructorRating.query.delete()
    Enrollment.query.delete()
    Group.query.delete()
    Course.query.delete()
    Student.query.delete()
    Instructor.query.delete()
    User.query.filter(User.email != 'admin@zhub.com').delete()
    db.session.commit()

def generate_users():
    print("Generating Users...")
    
    # Ensure default admin exists
    admin = User.query.filter_by(email='admin@zhub.com').first()
    if not admin:
        admin = User(email='admin@zhub.com', first_name='Default', last_name='Admin', role='admin', is_active=True)
        admin.set_password('admin123')
        db.session.add(admin)

    # Extra Admins
    for i in range(NUM_ADMINS):
        u = User(
            email=f'admin{i+1}@zhub.com',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            role='admin',
            phone=fake.phone_number()[:20],
            is_active=True
        )
        u.set_password('password')
        db.session.add(u)

    db.session.flush()

    # Instructors
    instructors = []
    specializations = ['Mathematics', 'Physics', 'Programming', 'Language', 'Art', 'Business', 'Music']
    for i in range(NUM_INSTRUCTORS):
        u = User(
            email=f'instructor{i+1}@zhub.com',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            role='instructor',
            phone=fake.phone_number()[:20],
            is_active=random.choices([True, False], weights=[90, 10])[0]
        )
        u.set_password('password')
        db.session.add(u)
        db.session.flush()

        inst = Instructor(
            user_id=u.id,
            specialization=random.choice(specializations),
            bio=fake.paragraph() if random.random() > 0.2 else None
        )
        db.session.add(inst)
        instructors.append(inst)

    # Students
    students = []
    for i in range(NUM_STUDENTS):
        u = User(
            email=f'student{i+1}@zhub.com',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            role='student',
            phone=fake.phone_number()[:20],
            is_active=random.choices([True, False], weights=[95, 5])[0]
        )
        u.set_password('password')
        db.session.add(u)
        db.session.flush()

        stu = Student(
            user_id=u.id,
            date_of_birth=fake.date_of_birth(minimum_age=12, maximum_age=60),
            guardian_phone=fake.phone_number()[:20] if random.random() > 0.3 else None,
            notes=fake.sentence() if random.random() > 0.8 else None,
            # New fields:
            gender=random.choice(['male', 'female']),
            nationality=fake.country(),
            address_line=fake.street_address(),
            city=fake.city(),
            country=fake.country(),
            emergency_contact_name=fake.name() if random.random() > 0.3 else None,
            emergency_contact_phone=fake.phone_number()[:20] if random.random() > 0.3 else None,
            school_name=fake.company() + ' School' if random.random() > 0.4 else None,
            grade=random.choice(['Grade 7','Grade 8','Grade 9','Grade 10','Grade 11','Grade 12',
                                 'Year 1','Year 2','Year 3','Freshman','Sophomore','Junior','Senior',None]),
        )
        
        # Enforce guardian_phone for minors
        from datetime import date as _date
        if stu.date_of_birth:
            today = _date.today()
            age = (today.year - stu.date_of_birth.year
                   - ((today.month, today.day) < (stu.date_of_birth.month, stu.date_of_birth.day)))
            if age < 18 and not stu.guardian_phone:
                stu.guardian_phone = fake.phone_number()[:20]

        db.session.add(stu)
        students.append(stu)
        
        # Batch commit to save memory
        if i % 100 == 0:
            db.session.commit()

    db.session.commit()
    return instructors, students

def generate_courses_and_groups(instructors):
    print("Generating Courses and Groups...")
    courses = []
    groups = []
    levels = ['beginner', 'intermediate', 'advanced']
    days = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    times = ['10:00 AM', '02:00 PM', '06:00 PM', '08:00 PM']

    for i in range(NUM_COURSES):
        base_fee = random.choice([0, 500, 1000, 2000, 5000])
        start = fake.date_between(start_date='-6m', end_date='today')
        duration_days = random.randint(4, 16) * 7
        end = start + timedelta(days=duration_days)
        total_h = random.choice([20, 30, 40, 60, 80, 100])
        num_sess = random.randint(10, int(total_h / 2))
        c = Course(
            name=f'{fake.catch_phrase()} {random.choice(["101", "Advanced", "Masterclass", "Basics"])}',
            description=fake.paragraph(),
            level=random.choice(levels),
            duration_weeks=random.randint(4, 16),
            start_date=start,
            end_date=end,
            total_hours=float(total_h),
            num_sessions=num_sess,
            reservation_fee=base_fee * 0.1,
            course_fee=base_fee,
            certificate_fee=random.choice([0, 50, 100]) if base_fee > 0 else 0,
            is_active=random.choices([True, False], weights=[90, 10])[0],
            created_at=fake.date_time_between(start_date='-2y', end_date='now')
        )
        db.session.add(c)
        db.session.flush()
        courses.append(c)

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        chosen_days = random.sample(days, random.randint(1, 3))
        for day in chosen_days:
            start_hr = random.choice([9, 10, 14, 16, 18])
            duration = random.choice([1, 1.5, 2, 2.5, 3])
            end_hr_minutes = int(start_hr * 60 + duration * 60)
            end_h = end_hr_minutes // 60
            end_m = end_hr_minutes % 60
            sched = CourseSchedule(
                course_id=c.id,
                weekday=day,
                start_time=f'{start_hr:02d}:00',
                end_time=f'{end_h:02d}:{end_m:02d}',
            )
            db.session.add(sched)

        # Groups for this course
        num_groups = random.randint(1, MAX_GROUPS_PER_COURSE)
        for g_idx in range(num_groups):
            g = Group(
                course_id=c.id,
                instructor_id=random.choice(instructors).id if random.random() > 0.1 else None,
                name=f'Group {chr(65 + g_idx)}',
                schedule_day=random.choice(days),
                schedule_time=random.choice(times),
                max_capacity=random.choice([10, 20, 30, 50]),
                is_active=c.is_active
            )
            db.session.add(g)
            db.session.flush()
            groups.append(g)
            
    db.session.commit()
    return courses, groups

def generate_enrollments(students, courses, groups):
    print("Generating Enrollments...")
    enrollments = []
    # Map course_id to its groups
    course_groups = {}
    for g in groups:
        if g.course_id not in course_groups:
            course_groups[g.course_id] = []
        course_groups[g.course_id].append(g)

    # Keep track of group current capacities
    group_counts = {g.id: 0 for g in groups}

    statuses = ['active', 'completed', 'dropped']
    
    for s in students:
        num_courses = random.randint(0, MAX_ENROLLMENTS_PER_STUDENT)
        # Select unique courses for this student
        student_courses = random.sample(courses, min(num_courses, len(courses)))
        
        for c in student_courses:
            if c.id not in course_groups or not course_groups[c.id]:
                continue
            
            # Find an available group
            available_groups = [g for g in course_groups[c.id] if group_counts[g.id] < g.max_capacity]
            if not available_groups:
                continue # Course is full
                
            g = random.choice(available_groups)
            
            status = random.choices(statuses, weights=[70, 20, 10])[0]
            if not c.is_active or not g.is_active:
                status = random.choice(['completed', 'dropped'])
                
            e = Enrollment(
                student_id=s.id,
                course_id=c.id,
                group_id=g.id,
                status=status,
                enrolled_at=fake.date_time_between(start_date='-1y', end_date='now')
            )
            db.session.add(e)
            enrollments.append(e)
            
            if status == 'active':
                group_counts[g.id] += 1
                
    db.session.commit()
    return enrollments

def generate_attendance(groups, enrollments):
    print("Generating Attendance...")
    admin = User.query.filter_by(role='admin').first()
    
    # Map group_id to its enrollments
    group_enrollments = {}
    for e in enrollments:
        if e.group_id not in group_enrollments:
            group_enrollments[e.group_id] = []
        group_enrollments[e.group_id].append(e)
        
    for g in groups:
        if g.id not in group_enrollments:
            continue
            
        # Simulate 1 to 20 past sessions for this group
        num_sessions = random.randint(1, 20)
        start_date = date.today() - timedelta(days=num_sessions * 7)
        
        # Decide an attendance pattern for the whole group (e.g. strict instructor vs lenient)
        group_presence_rate = random.uniform(0.6, 0.95)
        
        for i in range(num_sessions):
            session_date = start_date + timedelta(days=i * 7)
            
            # 5% chance the instructor forgot to mark attendance completely
            if random.random() < 0.05:
                continue
                
            for e in group_enrollments[g.id]:
                # If dropped, they might be absent for later sessions, or just not have records
                if e.status == 'dropped' and session_date > e.enrolled_at.date() + timedelta(days=14):
                    continue
                    
                status = 'present' if random.random() < group_presence_rate else 'absent'
                
                # Perfect attendance edge case (5% of students)
                if e.id % 20 == 0:
                    status = 'present'
                
                # Chronic absence edge case (5% of students)
                if e.id % 20 == 1:
                    status = 'absent'
                    
                att = Attendance(
                    enrollment_id=e.id,
                    group_id=g.id,
                    date=session_date,
                    status=status,
                    marked_by=g.instructor.user_id if g.instructor else admin.id
                )
                db.session.add(att)
                
        # Commit per group to manage memory
        db.session.commit()

def generate_payments_and_certificates(enrollments):
    print("Generating Transactions and Certificates...")
    admin = User.query.filter_by(role='admin').first()

    for e in enrollments:
        c = e.course
        s = e.student

        # If the course is free, maybe skip payments or just record 0
        if c.course_fee > 0:
            # Reservation fee
            if c.reservation_fee > 0 and random.random() > 0.1:
                p_res = Transaction(
                    student_id=s.id,
                    course_id=c.id,
                    transaction_kind='income',
                    income_type='reservation',
                    total_amount=c.reservation_fee,
                    paid_amount=c.reservation_fee,
                    recorded_by=admin.id,
                    date=e.enrolled_at
                )
                db.session.add(p_res)

            # Course fee (Full or partial)
            if random.random() > 0.2:
                amount = c.course_fee if random.random() > 0.3 else c.course_fee * 0.5
                p_course = Transaction(
                    student_id=s.id,
                    course_id=c.id,
                    transaction_kind='income',
                    income_type='course',
                    total_amount=amount,
                    paid_amount=amount,
                    recorded_by=admin.id,
                    date=e.enrolled_at + timedelta(days=random.randint(1, 14))
                )
                db.session.add(p_course)

            # Certificate fee (Usually paid if completed)
            if e.status == 'completed' and c.certificate_fee > 0 and random.random() > 0.1:
                p_cert = Transaction(
                    student_id=s.id,
                    course_id=c.id,
                    transaction_kind='income',
                    income_type='certificate',
                    total_amount=c.certificate_fee,
                    paid_amount=c.certificate_fee,
                    recorded_by=admin.id,
                    date=e.enrolled_at + timedelta(days=c.duration_weeks * 7)
                )
                db.session.add(p_cert)

                # Generate Certificate
                cert = Certificate(
                    student_id=s.id,
                    course_id=c.id,
                    file_path=f'certificates/cert_fake_{s.id}_{c.id}.pdf',
                    issued_at=p_cert.date + timedelta(days=1)
                )
                db.session.add(cert)
        
        elif e.status == 'completed' and c.certificate_fee == 0:
            # Generate free certificate
            cert = Certificate(
                student_id=s.id,
                course_id=c.id,
                file_path=f'certificates/cert_fake_{s.id}_{c.id}.pdf',
                issued_at=e.enrolled_at + timedelta(days=c.duration_weeks * 7)
            )
            db.session.add(cert)

        # Batch commit
        if e.id % 100 == 0:
            db.session.commit()
            
    db.session.commit()

def generate_ratings_and_performance(enrollments):
    print("Generating Ratings and Performance...")
    
    rated_courses = set()
    rated_instructors = set()
    
    for e in enrollments:
        if e.status == 'completed':
            # Performance evaluation
            if random.random() > 0.3:
                perf = StudentPerformance(
                    enrollment_id=e.id,
                    score=random.uniform(50.0, 100.0),
                    feedback=fake.sentence() if random.random() > 0.5 else None,
                    evaluated_by=e.group.instructor.user_id if e.group.instructor else None
                )
                db.session.add(perf)
                
            # Course Rating
            c_key = (e.student_id, e.course_id)
            if c_key not in rated_courses and random.random() > 0.4:
                c_rating = CourseRating(
                    student_id=e.student_id,
                    course_id=e.course_id,
                    rating=random.randint(1, 5),
                    comment=fake.sentence() if random.random() > 0.5 else None
                )
                db.session.add(c_rating)
                rated_courses.add(c_key)
            
            # Instructor Rating
            if e.group.instructor_id:
                i_key = (e.student_id, e.group.instructor_id)
                if i_key not in rated_instructors and random.random() > 0.4:
                    i_rating = InstructorRating(
                        student_id=e.student_id,
                        instructor_id=e.group.instructor_id,
                        rating=random.randint(1, 5),
                        comment=fake.sentence() if random.random() > 0.5 else None
                    )
                    db.session.add(i_rating)
                    rated_instructors.add(i_key)
                    
    db.session.commit()

def generate_kpi_data(students, courses, enrollments):
    print("Generating KPI data (assignments, submissions, participation, evaluations, notes)...")
    admin = User.query.filter_by(role='admin').first()

    # --- Assignments per course ---
    assignment_map = {}  # course_id -> list of Assignment
    for c in courses:
        num_asgn = random.randint(0, 4)
        course_assignments = []
        for i in range(num_asgn):
            asgn = Assignment(
                course_id=c.id,
                title=f'{fake.bs().title()} Assignment {i+1}',
                description=fake.sentence() if random.random() > 0.5 else None,
                due_date=fake.date_between(start_date='-3m', end_date='today'),
                created_by=admin.id,
            )
            db.session.add(asgn)
            course_assignments.append(asgn)
        assignment_map[c.id] = course_assignments
    db.session.flush()

    # --- Assignment Submissions per student ---
    for e in enrollments:
        for asgn in assignment_map.get(e.course_id, []):
            status = random.choices(
                ['delivered', 'partial', 'not_delivered'], weights=[60, 20, 20]
            )[0]
            sub = AssignmentSubmission(
                assignment_id=asgn.id,
                student_id=e.student_id,
                status=status,
                recorded_by=admin.id,
            )
            db.session.add(sub)

    db.session.commit()

    # --- Participation scores on existing Attendance records ---
    from website.models import Attendance as Att
    all_att = Att.query.all()
    for att in all_att:
        if att.status == 'present' and random.random() > 0.3:
            att.participation_score = round(random.uniform(5.0, 10.0), 1)
    db.session.commit()

    # --- Trainer Evaluations ---
    for e in enrollments:
        if e.status == 'completed' and random.random() > 0.4:
            if e.group.instructor:
                existing = TrainerEvaluation.query.filter_by(
                    enrollment_id=e.id, instructor_id=e.group.instructor_id
                ).first()
                if not existing:
                    ev = TrainerEvaluation(
                        student_id=e.student_id,
                        enrollment_id=e.id,
                        instructor_id=e.group.instructor_id,
                        score=round(random.uniform(50.0, 100.0), 1),
                        feedback=fake.sentence() if random.random() > 0.5 else None,
                        evaluated_by=admin.id,
                    )
                    db.session.add(ev)
    db.session.commit()

    # --- Portfolio Projects ---
    skills_pool = ['Python','Flask','HTML','CSS','JavaScript','React','SQL',
                   'Photoshop','Illustrator','UI Design','Data Analysis',
                   'Machine Learning','Arduino','3D Modeling','Video Editing']
    for s in random.sample(students, min(len(students), 100)):
        num_proj = random.randint(0, 3)
        for i in range(num_proj):
            skills = random.sample(skills_pool, random.randint(2, 5))
            proj = StudentProject(
                student_id=s.id,
                title=fake.catch_phrase(),
                description=fake.paragraph() if random.random() > 0.3 else None,
                skills_used=', '.join(skills),
                project_link=fake.url() if random.random() > 0.6 else None,
                completion_status=random.choice(['completed','partial','not_completed','not_evaluated']),
                completion_score=round(random.uniform(50, 100), 1) if random.random() > 0.4 else None,
                instructor_remark=fake.sentence() if random.random() > 0.5 else None,
                created_by=admin.id,
            )
            db.session.add(proj)
    db.session.commit()

    # --- Instructor Notes ---
    all_instructors = Instructor.query.all()
    all_courses = Course.query.filter_by(is_active=True).all()
    for s in random.sample(students, min(len(students), 80)):
        num_notes = random.randint(0, 3)
        for _ in range(num_notes):
            note = InstructorNote(
                student_id=s.id,
                instructor_id=random.choice(all_instructors).id,
                course_id=random.choice(all_courses).id,
                body=fake.paragraph(),
                created_by=admin.id,
            )
            db.session.add(note)
    db.session.commit()
    print("KPI data generation complete.")


if __name__ == '__main__':
    with app.app_context():
        clear_db()
        instructors, students = generate_users()
        courses, groups = generate_courses_and_groups(instructors)
        enrollments = generate_enrollments(students, courses, groups)
        generate_attendance(groups, enrollments)
        generate_payments_and_certificates(enrollments)
        generate_ratings_and_performance(enrollments)
        generate_kpi_data(students, courses, enrollments)
        print("Data generation complete!")
