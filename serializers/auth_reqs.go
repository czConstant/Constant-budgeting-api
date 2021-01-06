package serializers

type RegisterReq struct {
	Email       string `json:"email"`
	Password    string `json:"password"`
	FirstName   string `json:"first_name"`
	MiddleName  string `json:"middle_name"`
	LastName    string `json:"last_name"`
	CompanyName string `json:"company_name"`
}

type LoginReq struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}
