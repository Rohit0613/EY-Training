Create database patienthealth1;
use patienthealth1;

create table patients(
PatientID Varchar(10) Primary key,
Name Varchar(50),
Age int,
Gender Varchar(50),
condiition Varchar(50)
);


create table doctors(
DoctorID Varchar(10) Primary key,
Name Varchar(50),
Specialization Varchar(50)
); 

CREATE TABLE visits (
  VisitID VARCHAR(10) PRIMARY KEY,
  PatientID VARCHAR(10),
  DoctorID VARCHAR(10),
  Date DATE,
  Cost DECIMAL(10,2),
  FOREIGN KEY (PatientID) REFERENCES patients(PatientID),
  FOREIGN KEY (DoctorID) REFERENCES doctors(DoctorID)
);


INSERT INTO patients(PatientID, Name, Age, condiition) VALUES
('P001','Neha',32,'Fever'),
('P002','Arjun',45,'Diabetes'),
('P003','Sophia',28,'Hypertension'),
('P004','Ravi',52,'Asthma'),
('P005','Meena',38,'Arthritis');


INSERT INTO doctors(DoctorID, Name, Specialization) VALUES
('D101','Dr. Patel','General Physician'),
('D102','Dr. Khan','Endocrinologist'),
('D103','Dr. Verma','Cardiologist'),
('D104','Dr. Rao','Pulmonologist');
