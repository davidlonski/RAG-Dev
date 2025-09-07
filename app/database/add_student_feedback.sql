-- Migration to add student_feedback column to submissions table
-- Run this command in your MySQL session

ALTER TABLE submissions 
ADD COLUMN student_feedback LONGTEXT NULL 
AFTER summary;

-- Verify the column was added
DESCRIBE submissions;
