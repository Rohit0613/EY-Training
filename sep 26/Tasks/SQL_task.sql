create table employee(
id int auto_increment primary key ,
name varchar(50),
age int,
department varchar(50),
salary decimal(10,2));

insert into employee (name,age,department,salary) values (("soham",22,"IT",45000),("yash",22,"DS",50000),("raviraj",22,"HR",50000));

select * from employee;

update employee
set salary=10000 
where id=1;

delete from employee where id =3;

select * from (select * from employee
order by salary 
limit 1)
order by salary desc 
limit 2;

select * from ( select * from employee order by salary desc limit 2) as tble
order by salary asc limit 1; 
