// @ts-ignore
export const mul = ({ x, y }, /** @type {number} */ scalar) => ({ x: x * scalar, y: y * scalar });

// @ts-ignore
export const div = ({ x, y }, /** @type {number} */ scalar) => ({ x: x / scalar, y: y / scalar });

export const index = (/** @type {string | any[]} */ array, /** @type {number} */ idx) => {
  idx -= Math.floor(idx / array.length) * array.length;
  if (idx < 0) idx += array.length;
  return idx;
};

export const combination = (/** @type {number} */ p, /** @type {number} */ n) => factorial(n) / (factorial(p) * factorial(n - p));

export const factorial = (/** @type {number} */ n) => {
  let result = 1;
  for (let i = 1; i <= n; ++i) {
    result = result * i;
  }
  return result;
};

export const readAsCSV = (/** @type {Blob} */ file) => {
  return new Promise(resolve => {
    const reader = new FileReader();
		// @ts-ignore
    reader.onload = ({ target: { result } }) => {
      resolve(result.split(/\r*\n/g).map((/** @type {string} */ row) => row.split(',')));
    };
    reader.readAsText(file);
  });
};

export const deepCopy = (/** @type {any} */ data) => JSON.parse(JSON.stringify(data));
