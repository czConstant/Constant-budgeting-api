package logger

import (
	"os"
	"path/filepath"
	"runtime/debug"

	"github.com/czConstant/constant-budgeting-api/errs"
	"github.com/czConstant/constant-budgeting-api/helpers"
	"github.com/czConstant/constant-core/domain"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

const (
	LOGGER_API_RESPONSE_TIME     = "api_response_time"
	LOGGER_API_APP_PANIC         = "api_app_panic"
	LOGGER_API_APP_ERROR         = "api_app_error"
	LOGGER_API_APP_REQUEST_ERROR = "api_app_request_error"
)

var logger *zap.Logger

func NewLogger(appName string, logPath string, stdout bool) {
	var err error
	outputPaths := []string{}
	if stdout {
		outputPaths = append(outputPaths, "stdout")
	}
	if logPath != "" {
		dir := filepath.Dir(logPath)
		parent := filepath.Base(dir)
		_, err = os.Stat(parent)
		if os.IsNotExist(err) {
			err = os.Mkdir(parent, os.ModePerm)
			if err != nil {
				panic(err)
			}
		}
		err = os.Chmod(parent, os.ModePerm)
		if err != nil {
			panic(err)
		}
		os.OpenFile(logPath, os.O_RDONLY|os.O_CREATE|os.O_APPEND, 0666)
		outputPaths = append(outputPaths, logPath)
	}
	cfg := zap.NewProductionConfig()
	cfg.OutputPaths = outputPaths
	cfg.InitialFields = map[string]interface{}{
		"app_name": appName,
	}
	logger, err = cfg.Build(
		zap.AddCallerSkip(1),
	)
	if err != nil {
		panic(err)
	}
}

func Sync() error {
	return logger.Sync()
}

func Info(category string, msg string, fields ...zap.Field) {
	logger.With(zap.String("app_category", category)).Info(msg, fields...)
}

func Fatal(msg string, fields ...zap.Field) {
	logger.Fatal(msg, fields...)
}

func Error(category string, msg string, fields ...zap.Field) {
	logger.
		WithOptions(zap.AddStacktrace(zap.DebugLevel)).
		With(zap.String("app_category", category)).
		Error(msg, fields...)
}

func WrapError(category string, err error, fields ...zap.Field) error {
	if err == nil {
		return nil
	}
	logger.
		WithOptions(zap.AddStacktrace(zap.DebugLevel)).
		With(zap.String("app_category", category)).
		With(zap.Any("error", err)).
		Error(err.Error(), fields...)
	return err
}

func WrapCaptureError(err error, fields ...zap.Field) error {
	if err == nil {
		return nil
	}
	logger.
		WithOptions(zap.AddStacktrace(zap.DebugLevel)).
		With(zap.String("app_category", LOGGER_API_APP_ERROR)).
		With(zap.Any("error", err)).
		Error(err.Error(), fields...)
	return err
}

func WrapStacktraceError(err *errs.Error, extras ...interface{}) error {
	if err == nil {
		return nil
	}
	err = &errs.Error{
		Code:    err.Code,
		Message: err.Message,
	}
	err.SetStacktrace(string(debug.Stack()))
	if len(extras) > 0 {
		err.SetExtra(extras)
	}
	return err
}

func WrapHttpRequestError(c *gin.Context, reqObj interface{}, err error) error {
	if err == nil {
		return nil
	}
	_, ok := err.(*errs.Error)
	var stacktrace string
	if ok {
		stacktrace = string(err.(*errs.Error).Stacktrace())
	} else {
		stacktrace = string(debug.Stack())
	}
	u, ok := c.Get("context_user_data")
	var userID uint
	var email string
	if ok {
		user := u.(*domain.User)
		if user != nil {
			userID = user.ID
			email = user.Email
		}
	}
	logger.
		With(zap.String("app_category", LOGGER_API_APP_REQUEST_ERROR)).
		With(zap.Any("error", err)).
		Info(
			err.Error(),
			zap.Any("ip", c.ClientIP()),
			zap.Any("method", c.Request.Method),
			zap.Any("path", c.Request.URL.Path),
			zap.Any("raw_query", c.Request.URL.RawQuery),
			zap.Any("status", c.Writer.Status()),
			zap.Any("user_agent", c.Request.UserAgent()),
			zap.Any("user_id", userID),
			zap.Any("email", email),
			zap.Any("stacktrace", stacktrace),
			zap.Any("request_body_json", helpers.ConvertJsonString(reqObj)),
		)
	return err
}

func Debug(msg string, fields ...zap.Field) {
	logger.Debug(msg, fields...)
}

func Panic(msg string, fields ...zap.Field) {
	logger.Panic(msg, fields...)
}
