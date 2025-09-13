-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    role VARCHAR(20) CHECK (role IN ('teacher', 'student')) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    last_login TIMESTAMP,
    status VARCHAR(20) CHECK (status IN ('active', 'inactive')) NOT NULL DEFAULT 'active'
);

-- RAG Quizzers table
CREATE TABLE rag_quizzers (
    id SERIAL PRIMARY KEY,
    teacher_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    name VARCHAR(255) NOT NULL,
    collection_id VARCHAR(255) NOT NULL,
    presentation_name VARCHAR(255) NOT NULL,
    num_slides INT NOT NULL,
    num_text_items INT NOT NULL DEFAULT 0,
    num_image_items INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    status VARCHAR(20) CHECK (status IN ('active','archived')) NOT NULL DEFAULT 'active'
);

CREATE TABLE rag_quizzer_slides (
    id SERIAL PRIMARY KEY,
    rag_quizzer_id INT NOT NULL REFERENCES rag_quizzers(id) ON DELETE CASCADE ON UPDATE CASCADE,
    slide_number INT NOT NULL,
    slide_content TEXT,
    created_at TIMESTAMP NOT NULL
);

-- Assignments table
CREATE TABLE assignments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    collection_id VARCHAR(255),
    teacher_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    created_at TIMESTAMP NOT NULL,
    num_questions INT NOT NULL,
    num_text_questions INT NOT NULL,
    num_image_questions INT NOT NULL,
    status VARCHAR(20) CHECK (status IN ('active','archived')) NOT NULL DEFAULT 'active'
);

-- Images table
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    image_data BYTEA NOT NULL,
    image_extension VARCHAR(12),
    created_at TIMESTAMP NOT NULL,
    file_size INT,
    content_type VARCHAR(100)
);

-- Questions table
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    assignment_id INT NOT NULL REFERENCES assignments(id) ON DELETE CASCADE ON UPDATE CASCADE,
    type VARCHAR(20) CHECK (type IN ('text','image')) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    context TEXT,
    image_id INT REFERENCES images(id) ON DELETE SET NULL ON UPDATE CASCADE,
    created_at TIMESTAMP NOT NULL
);

-- Submissions table
CREATE TABLE submissions (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    assignment_id INT NOT NULL REFERENCES assignments(id) ON DELETE CASCADE ON UPDATE CASCADE,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    overall_score FLOAT,
    summary TEXT,
    student_feedback TEXT,
    status VARCHAR(20) CHECK (status IN ('in_progress','completed')) NOT NULL DEFAULT 'in_progress'
);

-- Submission answers table
CREATE TABLE submission_answers (
    id SERIAL PRIMARY KEY,
    submission_id INT NOT NULL REFERENCES submissions(id) ON DELETE CASCADE ON UPDATE CASCADE,
    question_id INT NOT NULL REFERENCES questions(id) ON DELETE CASCADE ON UPDATE CASCADE,
    attempt_number SMALLINT NOT NULL,
    student_answer TEXT NOT NULL,
    grade SMALLINT NOT NULL,
    feedback TEXT,
    created_at TIMESTAMP NOT NULL,
    CONSTRAINT uq_submission_attempt UNIQUE (submission_id, question_id, attempt_number)
);
