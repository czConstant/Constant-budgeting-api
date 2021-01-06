package apis

import (
	"time"

	"github.com/czConstant/constant-budgeting-api/logger"
	"github.com/czConstant/constant-budgeting-api/services"
	"github.com/getsentry/raven-go"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/binding"
)

type Server struct {
	g  *gin.Engine
	us *services.User
}

func NewServer(
	g *gin.Engine,
	us *services.User,
) *Server {
	return &Server{
		g:  g,
		us: us,
	}
}

func (s *Server) Routers() {
	s.g.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://*", "https://*"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
		AllowOriginFunc:  func(origin string) bool { return true },
		AllowMethods:     []string{"GET", "POST", "PUT", "HEAD", "OPTIONS", "DELETE"},
		AllowHeaders:     []string{"*"},
		MaxAge:           12 * time.Hour,
	}))
	s.g.Use(s.recoveryMiddleware(raven.DefaultClient, false))
	s.g.Use(s.logApiMiddleware())
	budgetingAPI := s.g.Group("/budgeting-api")
	{
		budgetingAPI.GET("/", func(c *gin.Context) {
			c.JSON(200, gin.H{
				"result": "OK",
			})
		})
	}
}

func (s *Server) ShouldBindJSON(c *gin.Context, obj interface{}) error {
	return logger.WrapHttpRequestError(c, nil, c.ShouldBindWith(obj, binding.JSON))
}
