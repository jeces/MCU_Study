var express = require('express')	//해당 경로의 모듈을 추출한다. 그냥 express를 가져와서 express에 저장[프레임워크로서 node에서 간단하게 server를 띄울 수 있는 웹프레임워크]
var http = require('http')    		//위와 마찬가지
var app = express()					//app으로 express 실행
var server = http.createServer(app);	//서버가 app을 이용하여 서버를 생성

var bodyParser = require('body-parser');
var Gpio = require('onoff').Gpio;
var led1 = new Gpio(20, 'out');
var led2 = new Gpio(21, 'out');

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended : false}));
app.get('/', function(req, res) {
	res.sendfile('controlLedhtml.html', {root : __dirname});
});

app.post('/data', function(req, res) {	// /data에 post로 값을 받을 경우 실행 됨
	var state = req.body.led;			// 수신된 값중 body의 led 부분의 값을 변수 state에 저장한 후 처리(즉 버튼 on off)
	if(state == 'LED ON') {					// on상태가 되면
		led1.writeSync(1);				// led1 on 비동기식으로 GPIO 데이터씀
		led2.writeSync(1);				// led2 off 비동기식으로 GPIO 데이터씀
	}
	else {								// off상태가 되면
		led1.writeSync(0);				// led1 off 비동기식
		led2.writeSync(0);				// led2 off 비동기식
	}
	console.log(state);					// 콘솔창에 on off 띄워줌
	res.sendfile('controlLedhtml.html', {root : __dirname});
});

server.listen(9090, function() {											//포트 9090으로 설정 완료되면 아래 문자 띄움
	console.log('express server listening on port ' + server.address().port)
});
