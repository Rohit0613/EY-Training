create database retailDB;
use retailDB;
 
Create table Customers(
customer_id int auto_increment primary key,
name varchar(50),
city varchar(40),
phone varchar(15));
 
Create table Products(
product_id int auto_increment primary key,
product_name varchar(50),
category varchar(40),
price decimal(10,2)
);
 
Create table Orders(
order_id int auto_increment primary key,
customer_id int,
order_date Date,
foreign key(customer_id) references Customers(customer_id));

Create table OrderDetails (
order_detail_id int auto_increment primary key,
order_id int,
product_id int,
qunatity int,
foreign key(order_id) references Orders(order_id),
foreign key(product_id)references Products(product_id));


INSERT INTO Customers (name, city, phone) VALUES
('Rahul', 'Mumbai', '9876543210'),
('Priya', 'Delhi', '9876501234'),
('Arjun', 'Bengaluru', '9876512345'),
('Neha', 'Hyderabad', '9876523456');


INSERT INTO Products (product_name, category, price) VALUES
('Laptop', 'Electronics', 60000.00),
('Smartphone', 'Electronics', 30000.00),
('Headphones', 'Accessories', 2000.00),
('Shoes', 'Fashion', 3500.00),
('T-Shirt', 'Fashion', 1200.00);


INSERT INTO Orders (customer_id, order_date) VALUES
(1, '2025-09-01'),
(2, '2025-09-02'),
(3, '2025-09-03'),
(1, '2025-09-04');


INSERT INTO OrderDetails (order_id, product_id, qunatity) VALUES
(1, 1, 1),   -- Rahul bought 1 Laptop
(1, 3, 2),   -- Rahul bought 2 Headphones
(2, 2, 1),   -- Priya bought 1 Smartphone
(3, 4, 1),   -- Arjun bought 1 Shoes
(4, 5, 3);   -- Rahul bought 3 T-Shirts

DELIMITER $$
create procedure get_products()
BEGIN
	select *
    from products;
END$$
delimiter ;

CALL get_products

delimiter $$

create procedure get_customerby_product()
begin 
	select o.order_id,o.order_date,c.name as Customer_name
    from orders o 
    join customers c 
    on c.customer_id =o.customer_id;
end $$

delimiter ;
call get_customerby_product()

delimiter $$
create procedure Get_FullOrderDetails()
begin 
	select o.order_id,
		c.name as customer_name,
		p.product_name,
		od.qunatity,
		p.price,
		(od.qunatity*p.price) as total
	from orders o
    join customers c on c.customer_id=o.customer_id
    join OrderDetails od on od.order_id=o.order_id
    join products p on p.product_id= od.product_id;
end $$

delimiter ;
call Get_FullOrderDetails()
 
 -- passing value
 
delimiter $$
create procedure GetFullOrderbyCust_id(in cust_id int)
begin 
	select o.order_id,
		p.product_name,
		od.qunatity,
		p.price,
		(od.qunatity*p.price) as total
	from orders o
    join OrderDetails od on od.order_id=o.order_id
    join products p on p.product_id= od.product_id
    where o.customer_id= cust_id;
end $$

delimiter ;
call GetFullOrderbyCust_id(1)

-- total sales by month and year 

delimiter $$
create procedure salesbydate(in month_no int, in year_no int)
begin 
	select month(o.order_date) as month,year(o.order_date) as year,
    sum(od.qunatity *p.price) as total_sales
    from orders o 
    join OrderDetails od on o.order_id=od.order_id
    join products p on od.product_id=p.product_id
    where month(o.order_date)=month_no and year(o.order_date) = year_no
    group by month,year;
end $$

delimiter ;
call salesbydate(9,2025);


