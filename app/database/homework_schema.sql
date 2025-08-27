-- User management tables
CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  email VARCHAR(255) NULL,
  first_name VARCHAR(255) NOT NULL,
  last_name VARCHAR(255) NOT NULL,
  role ENUM('teacher','student') NOT NULL,
  created_at DATETIME NOT NULL,
  last_login DATETIME NULL,
  status ENUM('active','inactive') NOT NULL DEFAULT 'active'
);

-- RAG Quizzer management tables
CREATE TABLE rag_quizzers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  teacher_id INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  collection_id VARCHAR(255) NOT NULL,
  presentation_name VARCHAR(255) NOT NULL,
  num_slides INT NOT NULL,
  num_text_items INT NOT NULL DEFAULT 0,
  num_image_items INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL,
  status ENUM('active','archived') NOT NULL DEFAULT 'active',
  FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE rag_quizzer_slides (
  id INT PRIMARY KEY AUTO_INCREMENT,
  rag_quizzer_id INT NOT NULL,
  slide_number INT NOT NULL,
  slide_content LONGTEXT NULL,
  created_at DATETIME NOT NULL,
  FOREIGN KEY (rag_quizzer_id) REFERENCES rag_quizzers(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Update assignments table to include teacher_id foreign key
CREATE TABLE assignments (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  collection_id VARCHAR(255) NULL,
  teacher_id INT NOT NULL,
  created_at DATETIME NOT NULL,
  num_questions INT NOT NULL,
  num_text_questions INT NOT NULL,
  num_image_questions INT NOT NULL,
  status ENUM('active','archived') NOT NULL DEFAULT 'active',
  FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE questions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  assignment_id INT NOT NULL,
  type ENUM('text','image') NOT NULL,
  question LONGTEXT NOT NULL,
  answer LONGTEXT NOT NULL,
  context LONGTEXT NULL,
  image_bytes LONGBLOB NULL,
  image_extension VARCHAR(12) NULL,
  created_at DATETIME NOT NULL,
  FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Update submissions table to include student_id foreign key
CREATE TABLE submissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    assignment_id INT NOT NULL,
    started_at DATETIME NOT NULL,
    completed_at DATETIME NULL,
    overall_score FLOAT NULL,
    summary LONGTEXT NULL,
    status ENUM('in_progress','completed') NOT NULL DEFAULT 'in_progress',
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE submission_answers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  submission_id INT NOT NULL,
  question_id INT NOT NULL,
  attempt_number TINYINT NOT NULL,
  student_answer LONGTEXT NOT NULL,
  grade TINYINT NOT NULL,
  feedback LONGTEXT NULL,
  created_at DATETIME NOT NULL,
  FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE ON UPDATE CASCADE,
  UNIQUE KEY uq_submission_attempt (submission_id, question_id, attempt_number)
);