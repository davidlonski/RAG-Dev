

EXPLAIN CREATE TABLE IF NOT EXISTS submissions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  student_id VARCHAR(255) NOT NULL,
  assignment_id INT NOT NULL,
  started_at DATETIME NOT NULL,
  completed_at DATETIME NULL,
  overall_score FLOAT NULL,
  summary LONGTEXT NULL,
  status ENUM('in_progress','completed') NOT NULL DEFAULT 'in_progress',
  CONSTRAINT fk_sub_assignment FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
  INDEX idx_sub_student (student_id),
  INDEX idx_sub_assignment (assignment_id)
);

CREATE TABLE IF NOT EXISTS submission_answers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  submission_id INT NOT NULL,
  question_id INT NOT NULL,
  attempt_number TINYINT NOT NULL,
  student_answer LONGTEXT NOT NULL,
  grade TINYINT NOT NULL,
  feedback LONGTEXT NULL,
  created_at DATETIME NOT NULL,
  CONSTRAINT fk_sa_submission FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE,
  CONSTRAINT fk_sa_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
  UNIQUE KEY uq_submission_attempt (submission_id, question_id, attempt_number),
  INDEX idx_sa_submission (submission_id),
  INDEX idx_sa_question (question_id)
);