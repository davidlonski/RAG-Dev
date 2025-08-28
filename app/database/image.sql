images (
  id int NOT NULL AUTO_INCREMENT,
  image_data mediumblob NOT NULL,
  uploaded_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) 