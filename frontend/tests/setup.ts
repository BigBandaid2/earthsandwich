import '@testing-library/jest-dom';

// jsdom doesn't implement scrollTo — stub it so components that call it don't throw.
window.HTMLElement.prototype.scrollTo = function () {};
