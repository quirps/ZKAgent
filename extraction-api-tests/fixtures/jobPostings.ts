export const validPostings = {
  standard: `
    Senior Python Engineer at Acme Corp.
    Remote-first, US timezones. $160,000 - $200,000.
    Requirements: Python (5+ yrs), FastAPI, PostgreSQL, Docker.
    Nice to have: Kubernetes, Redis.
  `,
  noSalary: `
    Join our startup as a backend developer.
    Competitive compensation. 2+ years Python experience.
    Remote OK. Apply at jobs@startup.io
  `,
  multiCurrency: `
    Senior Backend Engineer - Paris, France (Hybrid).
    Salary: €90,000 - €120,000. Python, FastAPI, PostgreSQL required.
    Must have EU work authorization.
  `,
  conflicting: `
    Senior Frontend Engineer - Entry Level Welcome.
    3-5 years experience preferred but will consider new grads.
    JavaScript required. Salary $60k-$180k DOE. Hybrid NYC.
  `,
};

export const invalidPostings = {
  empty: "",
  whitespaceOnly: "     ",
  gibberish: "asdfjkl; qwerty 12345 !@#$%",
  tooShort: "Dev job.",
};