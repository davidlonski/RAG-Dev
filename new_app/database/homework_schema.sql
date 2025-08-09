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
  type ENUM('text','image') NOT NULL,
  question LONGTEXT NOT NULL,
  answer LONGTEXT NOT NULL,
  context LONGTEXT NULL,
  image_bytes LONGBLOB NULL,
  image_extension VARCHAR(12) NULL,
  created_at DATETIME NOT NULL
);
