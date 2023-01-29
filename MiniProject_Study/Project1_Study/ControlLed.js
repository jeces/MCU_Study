var express = require('express')	//�ش� ����� ����� �����Ѵ�. �׳� express�� �����ͼ� express�� ����[�����ӿ�ũ�μ� node���� �����ϰ� server�� ��� �� �ִ� �������ӿ�ũ]
var http = require('http')    		//���� ��������
var app = express()					//app���� express ����
var server = http.createServer(app);	//������ app�� �̿��Ͽ� ������ ����

var bodyParser = require('body-parser');
var Gpio = require('onoff').Gpio;
var led1 = new Gpio(20, 'out');
var led2 = new Gpio(21, 'out');

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended : false}));
app.get('/', function(req, res) {
	res.sendfile('controlLedhtml.html', {root : __dirname});
});

app.post('/data', function(req, res) {	// /data�� post�� ���� ���� ��� ���� ��
	var state = req.body.led;			// ���ŵ� ���� body�� led �κ��� ���� ���� state�� ������ �� ó��(�� ��ư on off)
	if(state == 'LED ON') {					// on���°� �Ǹ�
		led1.writeSync(1);				// led1 on �񵿱������ GPIO �����;�
		led2.writeSync(1);				// led2 off �񵿱������ GPIO �����;�
	}
	else {								// off���°� �Ǹ�
		led1.writeSync(0);				// led1 off �񵿱��
		led2.writeSync(0);				// led2 off �񵿱��
	}
	console.log(state);					// �ܼ�â�� on off �����
	res.sendfile('controlLedhtml.html', {root : __dirname});
});

server.listen(9090, function() {											//��Ʈ 9090���� ���� �Ϸ�Ǹ� �Ʒ� ���� ���
	console.log('express server listening on port ' + server.address().port)
});
