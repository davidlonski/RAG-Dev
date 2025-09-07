-- Reset Database Data While Maintaining Structure
-- Run these commands in your MySQL session

-- Disable foreign key checks temporarily
SET FOREIGN_KEY_CHECKS = 0;

-- Reset all tables (removes data but keeps structure)
TRUNCATE TABLE submission_answers;
TRUNCATE TABLE submissions;
TRUNCATE TABLE questions;
TRUNCATE TABLE assignments;
TRUNCATE TABLE images;
TRUNCATE TABLE rag_quizzer_slides;
TRUNCATE TABLE rag_quizzers;
TRUNCATE TABLE users;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Verify tables are empty but structure remains
SELECT 'Verification - Tables should be empty:' as info;
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'rag_quizzers', COUNT(*) FROM rag_quizzers
UNION ALL
SELECT 'assignments', COUNT(*) FROM assignments
UNION ALL
SELECT 'questions', COUNT(*) FROM questions
UNION ALL
SELECT 'submissions', COUNT(*) FROM submissions
UNION ALL
SELECT 'submission_answers', COUNT(*) FROM submission_answers
UNION ALL
SELECT 'images', COUNT(*) FROM images;

-- Show table structure to confirm it's intact
SELECT 'Table structure verification:' as info;
SHOW TABLES;
