package apis

import (
	"errors"
	"fmt"
	"net/http"
	"runtime/debug"
	"strconv"
	"strings"
	"time"

	"github.com/czConstant/constant-budgeting-api/errs"
	"github.com/czConstant/constant-budgeting-api/logger"
	"github.com/czConstant/constant-budgeting-api/models"
	"github.com/czConstant/constant-budgeting-api/serializers"
	"github.com/getsentry/raven-go"
	"go.uber.org/zap"

	"github.com/gin-gonic/gin"
	"github.com/pquerna/otp/totp"
)

const (
	CONTEXT_USER_DATA = "context_user_data"
)

func (s *Server) pagingFromContext(c *gin.Context) (int, int) {
	var (
		page  int
		limit int
		err   error
	)
	page, err = strconv.Atoi(c.DefaultQuery("page", "1"))
	if err != nil {
		page = 1
	}
	limit, err = strconv.Atoi(c.DefaultQuery("limit", "10"))
	if err != nil {
		limit = 10
	}
	if limit > 500 {
		limit = 500
	}
	return page, limit
}

func (s *Server) authorizeMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		auth := c.GetHeader("Authorization")
		auths := strings.Split(auth, " ")
		if len(auths) < 2 {
			c.AbortWithStatusJSON(http.StatusBadRequest, serializers.Resp{Error: logger.WrapHttpRequestError(c, nil, logger.WrapStacktraceError(errs.ErrBadRequest))})
			return
		}
		token := auths[1]
		if token == "" {
			c.AbortWithStatusJSON(http.StatusBadRequest, serializers.Resp{Error: logger.WrapHttpRequestError(c, nil, logger.WrapStacktraceError(errs.ErrBadRequest))})
			return
		}
		var user *models.User
		var err error
		var httpCode int
		for i := 0; i < 3; i++ {
			user, httpCode, err = s.us.GetUserMe(token)
			if err == nil {
				break
			} else {
				if httpCode == http.StatusUnauthorized {
					c.AbortWithStatusJSON(http.StatusUnauthorized, serializers.Resp{Error: logger.WrapHttpRequestError(c, nil, logger.WrapStacktraceError(errs.ErrInvalidCredentials))})
					return
				}
			}
		}
		if err != nil {
			c.AbortWithStatusJSON(http.StatusBadRequest, serializers.Resp{Error: logger.WrapHttpRequestError(c, nil, logger.WrapStacktraceError(errs.ErrBadRequest))})
			return
		}
		c.Set(CONTEXT_USER_DATA, user)
		c.Next()
	}
}

func (s *Server) otpFromContext(c *gin.Context) string {
	myOtp := c.GetHeader("OTP")
	return myOtp
}

func (s *Server) OTPMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		uM := s.userContext(c)
		user, err := s.us.GetCoreUser(uM.ID)
		if err != nil {
			c.AbortWithStatusJSON(http.StatusBadRequest, serializers.Resp{Error: logger.WrapHttpRequestError(c, nil, logger.WrapStacktraceError(errs.ErrBadRequest))})
			return
		}
		if user == nil {
			c.AbortWithStatusJSON(http.StatusBadRequest, serializers.Resp{Error: logger.WrapHttpRequestError(c, nil, logger.WrapStacktraceError(errs.ErrBadRequest))})
			return
		}
		if user.TwoFAOn == false {
			c.AbortWithStatusJSON(http.StatusBadRequest, serializers.Resp{Error: logger.WrapHttpRequestError(c, nil, logger.WrapStacktraceError(errs.ErrOTPIsInvalid))})
			return
		}
		myOtp := s.otpFromContext(c)
		if myOtp == "" {
			c.AbortWithStatusJSON(http.StatusBadRequest, serializers.Resp{Error: logger.WrapHttpRequestError(c, nil, logger.WrapStacktraceError(errs.ErrOTPIsInvalid))})
			return
		}
		valid := totp.Validate(myOtp, user.Secret)
		if !valid {
			c.AbortWithStatusJSON(http.StatusBadRequest, serializers.Resp{Error: logger.WrapHttpRequestError(c, nil, logger.WrapStacktraceError(errs.ErrOTPIsInvalid))})
			return
		}
		c.Next()
	}
}

func (s *Server) userContext(c *gin.Context) *models.User {
	u, ok := c.Get(CONTEXT_USER_DATA)
	if !ok {
		panic(errors.New("user is not found"))
	}
	uM, ok := u.(*models.User)
	if !ok {
		panic(errors.New("user is not found"))
	}
	if uM == nil ||
		uM.ID <= 0 {
		panic(errors.New("user is not found"))
	}
	return uM
}

func (s *Server) logApiMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Set("log", true)
		start := time.Now()
		c.Next()
		if c.GetBool("log") {
			end := time.Now()
			latency := float64(end.Sub(start)) / float64(time.Second)
			u, ok := c.Get(CONTEXT_USER_DATA)
			var userID uint
			var email string
			if ok {
				user := u.(*models.User)
				if user != nil {
					userID = user.ID
					email = user.Email
				}
			}
			logger.Info(
				logger.LOGGER_API_RESPONSE_TIME,
				"request info",
				zap.Any("ip", c.ClientIP()),
				zap.Any("method", c.Request.Method),
				zap.Any("path", c.Request.URL.Path),
				zap.Any("raw_query", c.Request.URL.RawQuery),
				zap.Any("latency", latency),
				zap.Any("status", c.Writer.Status()),
				zap.Any("user_agent", c.Request.UserAgent()),
				zap.Any("user_id", userID),
				zap.Any("email", email),
			)
		}
	}
}

func (s *Server) recoveryMiddleware(client *raven.Client, onlyCrashes bool) gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			flags := map[string]string{
				"endpoint": c.Request.RequestURI,
			}
			if rval := recover(); rval != nil {
				rvalStr := fmt.Sprint(rval)
				fmt.Println(rvalStr)
				debug.PrintStack()

				u, ok := c.Get(CONTEXT_USER_DATA)
				var userID uint
				var email string
				if ok {
					user := u.(*models.User)
					if user != nil {
						userID = user.ID
						email = user.Email
					}
				}
				logger.Info(
					logger.LOGGER_API_APP_PANIC,
					"server is panic",
					zap.Any("ip", c.ClientIP()),
					zap.Any("method", c.Request.Method),
					zap.Any("path", c.Request.URL.Path),
					zap.Any("raw_query", c.Request.URL.RawQuery),
					zap.Any("status", c.Writer.Status()),
					zap.Any("user_agent", c.Request.UserAgent()),
					zap.Any("error", rvalStr),
					zap.Any("stacktrace", string(debug.Stack())),
					zap.Any("user_id", userID),
					zap.Any("email", email),
				)

				client.CaptureMessage(rvalStr, flags, raven.NewException(errors.New(rvalStr), raven.NewStacktrace(2, 3, nil)),
					raven.NewHttp(c.Request))
				c.AbortWithStatusJSON(http.StatusBadRequest, serializers.Resp{
					Result: true,
					Error:  errs.ErrorWithMessage(errs.ErrSystemError, "system error"),
				})
			}
			if !onlyCrashes {
				for _, item := range c.Errors {
					client.CaptureMessage(item.Error(), flags, &raven.Message{
						Message: item.Error(),
						Params:  []interface{}{item.Meta},
					},
						raven.NewHttp(c.Request))
				}
			}
		}()

		c.Next()
	}
}
