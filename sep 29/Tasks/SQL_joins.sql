create database school;
use school;

create table teacher (
teacher_id int auto_increment primary key,
name varchar(50),
subject_id int);

create table subject (
subject_id int auto_increment primary key,
subject_name varchar(50));

INSERT INTO Subject (subject_name) VALUES
('Mathematics'),   -- id = 1
('Science'),       -- id = 2
('English'),       -- id = 3
('History'),       -- id = 4
('Geography');     -- id = 5 (no teacher yet)

INSERT INTO Teacher (name, subject_id) VALUES
('Rahul Sir', 1),   -- Mathematics
('Priya Madam', 2), -- Science
('Arjun Sir', NULL),-- No subject assigned
('Neha Madam', 3);  -- English

select t.teacher_id,t.name,s.subject_name from teacher t inner join subject s on s.subject_id=t.subject_id;

select t.teacher_id,t.name,s.subject_name from teacher t left join subject s on s.subject_id=t.subject_id;

select t.teacher_id,t.name,s.subject_name from teacher t right join subject s on s.subject_id=t.subject_id;

select t.teacher_id,t.name,s.subject_name from teacher t left join subject s on s.subject_id=t.subject_id
union
select t.teacher_id,t.name,s.subject_name from teacher t right join subject s on s.subject_id=t.subject_id;