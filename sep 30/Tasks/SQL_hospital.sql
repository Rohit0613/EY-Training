create database hospitalmanagement;

use hospitalmanagement;

create table patients(
patient_id INT PRIMARY KEY,
name VARCHAR(50),
age INT,
gender CHAR(1),
city VARCHAR(50));

create table doctors(
doctor_id INT PRIMARY KEY,
name VARCHAR(50),
specialization VARCHAR(50),
experience INT);

create table Appointments(
appointment_id INT PRIMARY KEY,
patient_id int,
doctor_id int,
appointment_date DATE,
status VARCHAR(20),
FOREIGN KEY (patient_id) references  Patients(patient_id),
FOREIGN KEY (doctor_id) references Doctors(doctor_id));

create table MedicalRecords (
record_id INT PRIMARY KEY,
patient_id INT, 
doctor_id INT,
diagnosis VARCHAR(100),
treatment VARCHAR(100),
date DATE,
FOREIGN KEY (patient_id) references Patients(patient_id),
FOREIGN KEY (doctor_id) references Doctors(doctor_id));

create table Billing(

bill_id INT PRIMARY KEY,
patient_id INT ,
amount DECIMAL(10,2),
bill_date DATE,
status VARCHAR(20),
FOREIGN KEY (patient_id) references Patients(patient_id));


INSERT INTO doctors (doctor_id, name, specialization, experience) VALUES
(1, 'Dr. Asha', 'Cardiology', 15),
(2, 'Dr. Rajiv', 'Orthopedics', 10),
(3, 'Dr. Neha', 'Pediatrics', 8),
(4, 'Dr. Arvind', 'Neurology', 12),
(5, 'Dr. Meera', 'Dermatology', 9);

INSERT INTO Patients (patient_id, name, age, gender, city) VALUES
(101, 'Rohan', 34, 'M', 'Mumbai'),
(102, 'Anjali', 28, 'F', 'Delhi'),
(103, 'Karthik ', 45, 'M', 'Hyderabad'),
(104, 'Sneha ', 52, 'F', 'Kochi'),
(105, 'Amit ', 60, 'M', 'Pune'),
(106, 'Priya ', 22, 'F', 'Jaipur'),
(107, 'Arjun ', 39, 'M', 'Ahmedabad'),
(108, 'Divya ', 31, 'F', 'Bengaluru'),
(109, 'Manoj ', 50, 'M', 'Nagpur'),
(110, 'Ritu ', 26, 'F', 'Kolkata');

INSERT INTO Appointments (appointment_id, patient_id, doctor_id, appointment_date, status) VALUES
(201, 101, 1, '2025-09-01', 'Completed'),
(202, 102, 2, '2025-09-03', 'Scheduled'),
(203, 103, 1, '2025-09-05', 'Completed'),
(204, 104, 3, '2025-09-07', 'Cancelled'),
(205, 105, 4, '2025-09-09', 'Completed'),
(206, 106, 1, '2025-09-11', 'Scheduled'),
(207, 107, 5, '2025-09-13', 'Completed'),
(208, 108, 2, '2025-09-15', 'Scheduled'),
(209, 109, 3, '2025-09-17', 'Completed'),
(210, 110, 1, '2025-09-19', 'Scheduled');

INSERT INTO MedicalRecords (record_id, patient_id, doctor_id, diagnosis, treatment, date) VALUES
(301, 101, 1, 'Hypertension', 'Beta blockers', '2025-09-01'),
(302, 103, 1, 'Arrhythmia', 'ECG monitoring', '2025-09-05'),
(303, 106, 1, 'Chest Pain', 'Angiography', '2025-09-11'),
(304, 110, 1, 'High Cholesterol', 'Statins', '2025-09-19'),
(305, 102, 2, 'Fracture', 'Cast application', '2025-09-03'),
(306, 108, 2, 'Joint Pain', 'Physiotherapy', '2025-09-15'),
(307, 104, 3, 'Fever', 'Paracetamol', '2025-09-07'),
(308, 109, 3, 'Cold', 'Antihistamines', '2025-09-17'),
(309, 105, 4, 'Migraine', 'Painkillers', '2025-09-09'),
(310, 107, 5, 'Acne', 'Topical creams', '2025-09-13');


INSERT INTO Billing (bill_id, patient_id, amount, bill_date, status) VALUES
(401, 101, 1500.00, '2025-09-01', 'Paid'),
(402, 102, 2000.00, '2025-09-03', 'Unpaid'),
(403, 103, 1800.00, '2025-09-05', 'Paid'),
(404, 104, 1200.00, '2025-09-07', 'Unpaid'),
(405, 105, 2500.00, '2025-09-09', 'Paid'),
(406, 106, 3000.00, '2025-09-11', 'Unpaid'),
(407, 107, 1000.00, '2025-09-13', 'Paid'),
(408, 108, 2200.00, '2025-09-15', 'Unpaid'),
(409, 109, 800.00, '2025-09-17', 'Paid'),
(410, 110, 1600.00, '2025-09-19', 'Unpaid');


-- 1. List all patients assigned to a cardiologist.

select p.name ,d.specialization from patients p 
join appointments a on p.patient_id = a.patient_id
join doctors d on d.doctor_id = a.doctor_id
where d.specialization="Cardiology";

-- 2. Find all appointments for a given doctor.

delimiter $$
create procedure getappointmentbydocid(in did int)
begin 
select a.appointment_id from appointments a 
where a.doctor_id = did;
end $$
delimiter ;

 
-- 3. Show unpaid bills of patients.

select b.patient_id,p.name,b.amount from billing b
join patients p on p.patient_id=b.patient_id
where status="Unpaid";

-- 4. Procedure: GetPatientHistory(patient_id) → returns all visits, diagnoses, and treatments for a patient.

DELIMITER $$

CREATE PROCEDURE GetPatientHistory__(IN pid INT)
BEGIN
    SELECT m.patient_id,a.appointment_id,m.diagnosis,m.treatment
    FROM MedicalRecords m
    JOIN Appointments a ON m.patient_id = a.patient_id
    WHERE m.patient_id = pid;
END $$

DELIMITER ;


call GetPatientHistory__(101)

-- 5. Procedure: GetDoctorAppointments(doctor_id) → returns all appointments for a doctor.
DELIMITER $$

CREATE PROCEDURE GetDoctorAppointmentss(IN did INT)
BEGIN
    SELECT d.doctor_id,a.appointment_id
    FROM appointments a
    JOIN doctors d on d.doctor_id= a.doctor_id
    WHERE a.doctor_id = did;
END $$

DELIMITER ;

call GetDoctorAppointmentss(1);
