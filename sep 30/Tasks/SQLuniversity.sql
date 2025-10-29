CREATE DATABASE UniversityDB;
USE UniversityDB;

-- Students Table
CREATE TABLE Students (
student_id INT PRIMARY KEY,
name VARCHAR(50),
city VARCHAR(50)
);

-- Courses Table
CREATE TABLE Courses (
course_id INT PRIMARY KEY,
course_name VARCHAR(50),
credits INT
);


CREATE TABLE Enrollments (
enroll_id INT PRIMARY KEY,
student_id INT,
course_id INT,
grade CHAR(2),
FOREIGN KEY (student_id) REFERENCES Students(student_id),
FOREIGN KEY (course_id) REFERENCES Courses(course_id)
);

INSERT INTO Students VALUES
(1, 'Rahul', 'Mumbai'),
(2, 'Priya', 'Delhi'),
(3, 'Arjun', 'Bengaluru'),
(4, 'Neha', 'Hyderabad'),
(5, 'Vikram', 'Chennai');

INSERT INTO Courses VALUES
(101, 'Mathematics', 4),
(102, 'Computer Science', 3),
(103, 'Economics', 2),
(104, 'History', 3);

INSERT INTO Enrollments VALUES
(1, 1, 101, 'A'),
(2, 1, 102, 'B'),
(3, 2, 103, 'A'),
(4, 3, 101, 'C'),
(5, 4, 102, 'B'),
(6, 5, 104, 'A');

-- 1. Create a stored procedure to list all students.

delimiter $$ 

create procedure getallstudents()
begin
	select c.name from students s;
end$$
delimiter ;
call getallstudents()

-- 2. Create a stored procedure to list all courses.
delimiter $$ 
create procedure getallcourses_()
begin
	select c.course_name from courses c;
end$$
delimiter ;
call getallcourses_()

-- 3. Create a stored procedure to find all students from a given city (take city as input).
delimiter $$ 
create procedure getallstudentsbycity(in city varchar(50))
begin
	select s.name , c.course_name from Students s, Courses c where ;
end$$
delimiter ;
call getallstudentsbycity("Mumbai")

-- 4. Create a stored procedure to list students with their enrolled courses.
delimiter $$ 
create procedure getallstudentsbycourse_()
begin
	select s.name,c.course_name from Students s ,Courses c , enrollments e where e.student_id = s.student_id and e.course_id =c.course_id;
end$$
delimiter ;
call getallstudentsbycourse_()

-- with joins
delimiter $$ 
create procedure getallstudentsbycourse_joins()
begin
	select s.name,c.course_name from enrollments e 
    join students s on  e.student_id =s.student_id
    join courses c on e.course_id = c.course_id;
end$$
delimiter ;
call getallstudentsbycourse_joins()

-- 5. Create a stored procedure to list all students enrolled in a given course (take course_id as input).
delimiter $$ 
create procedure getallstudentsbycourseid_(in cid int)
begin
	select s.name,c.course_name from enrollments e 
    join students s on  e.student_id =s.student_id
    join courses c on e.course_id = c.course_id
    where c.course_id= cid;
end$$
delimiter ;
call getallstudentsbycourseid_(101)

-- 6. Create a stored procedure to count the number of students in each course.
delimiter $$ 
create procedure getcountofcourse_()
begin
	select count(s.name) as count ,c.course_name from enrollments e 
    join students s on  e.student_id =s.student_id
    join courses c on e.course_id = c.course_id
    group by c.course_name;
end$$
delimiter ;
call getcountofcourse_()

-- 7. Create a stored procedure to list students with course names and grades.
delimiter $$ 
create procedure getstudentcoursegrade()
begin
	select s.name ,c.course_name ,e.grade from enrollments e 
    join students s on  e.student_id =s.student_id
    join courses c on e.course_id = c.course_id;
end$$
delimiter ;
call getstudentcoursegrade()

-- 8. Create a stored procedure to show all courses taken by a given student (take student_id as input).
delimiter $$ 
create procedure getstudentcoursebystdd(in sid int)
begin
	select s.name ,c.course_name from enrollments e 
    join students s on  e.student_id =s.student_id
    join courses c on e.course_id = c.course_id
    where s.student_id = sid;
end$$
delimiter ;
call getstudentcoursebystdd(1)


-- 6. Create a stored procedure to count the number of students in each course.
delimiter $$ 
create procedure getavgbycourse()
begin
	select count(e.grade) as count ,c.course_name from enrollments e 
    join students s on  e.student_id =s.student_id
    join courses c on e.course_id = c.course_id
    group by c.course_name;
end$$
delimiter ;
call getavgbycourse()



