package errs

import "github.com/czConstant/constant-budgeting-api/helpers"

var (
	ErrSystemError              = &Error{Code: -1001, Message: "system error"}
	ErrInvalidEmail             = &Error{Code: -1002, Message: "invalid email"}
	ErrInvalidPassword          = &Error{Code: -1003, Message: "invalid password"}
	ErrEmailNotExists           = &Error{Code: -1004, Message: "email doesn't exist"}
	ErrEmailAlreadyExists       = &Error{Code: -1005, Message: "email already exists"}
	ErrInvalidCredentials       = &Error{Code: -1006, Message: "invalid credentials"}
	ErrBadRequest               = &Error{Code: -1007, Message: "bad request"}
	ErrBadPermission            = &Error{Code: -1008, Message: "bad permission"}
	ErrBadBodyRequest           = &Error{Code: -1009, Message: "bad body request"}
	ErrVerificationTokenExpired = &Error{Code: -1010, Message: "verification token expired"}
	ErrOTPIsInvalid             = &Error{Code: -1045, Message: "OTP not matched or invalidated!"}

	ErrNotEnoughBalance = &Error{Code: -222001, Message: "not enough balance"}
	ErrThirdParty       = &Error{Code: -222002, Message: "third party error"}
)

type Error struct {
	Code       int    `json:"code"`
	Message    string `json:"message"`
	stacktrace string
	extra      []interface{}
}

func (e *Error) SetStacktrace(stacktrace string) {
	e.stacktrace = stacktrace
}

func (e *Error) Stacktrace() string {
	return e.stacktrace
}

func (e *Error) Error() string {
	return e.Message
}

func (e *Error) SetExtra(extra []interface{}) {
	e.extra = extra
}

func (e *Error) ExtraJson() string {
	return helpers.ConvertJsonString(e.extra)
}

func ErrorWithMessage(err *Error, message string) *Error {
	err = &Error{
		Code:    err.Code,
		Message: message,
	}
	return err
}
