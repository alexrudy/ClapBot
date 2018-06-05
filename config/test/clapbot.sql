INSERT INTO users (username, email, password, status)
VALUES
  ('test', 'test@example.com', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f', 'active'),
  (NULL, 'other@example.com', NULL, 'registered');

INSERT INTO clsite (name, enabled)
VALUES
  ('sfbay', 1),
  ('atlanta', 0);

INSERT INTO clarea (site_id, name)
VALUES
  ((SELECT id FROM clsite WHERE name = 'sfbay'), 'sfc'),
  ((SELECT id FROM clsite WHERE name = 'sfbay'), 'eby');

INSERT INTO clcategory (name, description)
VALUES
    ('hhh', 'all housing'),
    ('apa', 'Housing/Apartments for Rent');