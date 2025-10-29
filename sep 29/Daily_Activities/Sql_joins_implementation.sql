use companydb;

create table department(
dept_id int  auto_increment primary key ,
dept_name varchar(50));



create table employees(
id int auto_increment primary key ,
name varchar(50),
age int,
salary decimal(10,2),
dept_id int,
foreign key (dept_id) references department(dept_id));

insert into department (dept_name) values("IT"),("HR"),("finanace"),("sales");
select * from department;
select * from empl

INSERT INTO Employees (name, age, salary, dept_id) VALUES
('Rahul', 28, 55000, 1),   -- IT
('Priya', 32, 60000, 2),   -- HR
('Arjun', 25, 48000, 3),   -- Finance
('Neha', 30, 70000, 1),    -- IT
('Vikram', 35, 65000, 4);  -- Sales


SET SQL_SAFE_UPDATES = 0;

TRUNCATE TABLE employees;

ALTER TABLE employees DROP FOREIGN KEY employees_ibfk_1;
TRUNCATE TABLE employees;
TRUNCATE TABLE department;

INSERT INTO Department (dept_name) VALUES
('IT'),         -- id = 1
('HR'),         -- id = 2
('Finance'),    -- id = 3
('Sales'),      -- id = 4
('Marketing');  -- id = 5  

INSERT INTO Employees (name, age, salary, dept_id) VALUES
('Rahul', 28, 55000, 1),   -- IT
('Priya', 32, 60000, 2),   -- HR
('Arjun', 25, 48000, NULL),-- 
('Neha', 30, 70000, 1),    -- IT
('Vikram', 35, 65000, 4);  -- Sales

select e.name, e.salary, d.dept_name from employees e inner join department d on e.dept_id = d.dept_id;

select e.name, e.salary, d.dept_name from employees e left join department d on e.dept_id = d.dept_id;

select e.name, e.salary, d.dept_name from employees e right  join department d on e.dept_id = d.dept_id;

select e.name, e.salary, d.dept_name from employees e left join department d on e.dept_id = d.dept_id
union
select e.name, e.salary, d.dept_name from employees e right  join department d on e.dept_id = d.dept_id;