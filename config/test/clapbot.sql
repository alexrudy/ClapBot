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
  ((SELECT id FROM clsite WHERE name = 'sfbay'), 'eby'),
  ((SELECT id FROM clsite WHERE name = 'atlanta'), 'atl');

INSERT INTO clcategory (name, description)
VALUES
    ('hhh', 'all housing'),
    ('apa', 'Housing/Apartments for Rent'),
    ('swp', 'Housing Swap');

INSERT INTO housingsearch (name, description, target_date, expiration_date, cl_site, cl_area, cl_category, enabled)
VALUES
    ('Test 1', 'A valid test', datetime('now', '+7 Days'), datetime('now', '+30 Days'),
      (SELECT id FROM clsite WHERE name = 'sfbay'), (SELECT id FROM clarea WHERE name = 'eby'), (SELECT id FROM clcategory WHERE name = 'apa'), 1),
    ('Test 2', 'An expired test', datetime('now','-7 Days'), datetime('now', '-30 Days'),
      (SELECT id FROM clsite WHERE name = 'sfbay'), (SELECT id FROM clarea WHERE name = 'eby'), (SELECT id FROM clcategory WHERE name = 'swp'), 1),
    ('Test 3', 'An incomplete test', datetime('now', '+7 Days'), datetime('now', '+30 Days'),
      (SELECT id FROM clsite WHERE name = 'sfbay'), NULL, NULL, 1),
    ('Test 4', 'A disabled test', datetime('now', '+7 Days'), datetime('now', '+30 Days'),
      (SELECT id FROM clsite WHERE name = 'sfbay'), (SELECT id FROM clarea WHERE name = 'sfc'), (SELECT id FROM clcategory WHERE name = 'apa'), 0),
    ('Test 5', 'A second area', datetime('now', '+7 Days'), datetime('now', '+30 Days'),
      (SELECT id FROM clsite WHERE name = 'sfbay'), (SELECT id FROM clarea WHERE name = 'eby'), (SELECT id FROM clcategory WHERE name = 'hhh'), 1),
    ('Test 5', 'Atlanta test', datetime('now', '+7 Days'), datetime('now', '+30 Days'),
      (SELECT id FROM clsite WHERE name = 'atlanta'), (SELECT id FROM clarea WHERE name = 'atl'), (SELECT id FROM clcategory WHERE name = 'apa'), 1);
