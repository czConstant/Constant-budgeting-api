package serializers

type Resp struct {
	Result interface{} `json:"result"`
	Error  interface{} `json:"error"`
	Count  *uint       `json:"count,omitempty"`
}
