CREATE TABLE assignments (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  collection_id VARCHAR(255) NULL,
  created_at DATETIME NOT NULL,
  num_questions INT NOT NULL,
  num_text_questions INT NOT NULL,
  num_image_questions INT NOT NULL,
  status ENUM('active','archived') NOT NULL DEFAULT 'active'
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

CREATE TABLE submissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(255) NOT NULL,
    assignment_id INT, -- Define the column first
    started_at DATETIME NOT NULL,
    completed_at DATETIME NULL,
    overall_score FLOAT NULL,
    summary LONGTEXT NULL,
    status ENUM('in_progress','completed') NOT NULL DEFAULT 'in_progress',
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