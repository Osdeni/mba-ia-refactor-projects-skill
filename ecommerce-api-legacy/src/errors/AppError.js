'use strict';

class AppError extends Error {
  constructor(status, message) {
    super(message);
    this.name = this.constructor.name;
    this.status = status;
  }
}

class ValidationError extends AppError {
  constructor(message) { super(400, message); }
}

class PaymentDeniedError extends AppError {
  constructor(message) { super(400, message); }
}

class UnauthorizedError extends AppError {
  constructor(message) { super(401, message); }
}

class ForbiddenError extends AppError {
  constructor(message) { super(403, message); }
}

class NotFoundError extends AppError {
  constructor(message) { super(404, message); }
}

module.exports = {
  AppError,
  ValidationError,
  PaymentDeniedError,
  UnauthorizedError,
  ForbiddenError,
  NotFoundError,
};
