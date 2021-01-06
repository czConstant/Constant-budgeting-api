package apis

import (
	"net/http"

	"github.com/czConstant/constant-budgeting-api/serializers"
	"github.com/gin-gonic/gin"
)

func (s *Server) UserMe(c *gin.Context) {
	c.JSON(http.StatusOK, serializers.Resp{Result: true})
}
