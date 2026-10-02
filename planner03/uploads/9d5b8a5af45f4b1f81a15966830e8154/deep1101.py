# -*- coding: utf-8 -*-
"""
Created on Mon Nov  1 09:04:43 2021

@author: KITCOOP
deep1101.py
"""
#SimpleRNN 레이어 
import tensorflow as tf
import numpy as np
X = []
Y = []
for i in range(6):
    lst = list(range(i,i+4))
    X.append(list(map(lambda c: [c/10], lst)))
    Y.append((i+4)/10)

X = np.array(X)
Y = np.array(Y)    
for i in range(len(X)):
    print(np.squeeze(X[i]), Y[i])

model = tf.keras.Sequential([
    tf.keras.layers.SimpleRNN(units=10, return_sequences=False, input_shape=[4,1]),
    tf.keras.layers.Dense(1)
])
model.compile(optimizer='adam', loss='mse')
model.summary()
model.fit(X, Y, epochs=100,verbose=0)
print(model.predict(X))
#학습 안된 데이터 예측하기
print(model.predict(np.array([[[0.6],[0.7],[0.8],[0.9]]])))
print(model.predict(np.array([[[-0.1],[0.0],[0.1],[0.2]]])))
print(model.predict(np.array([[[2.],[3.],[4.],[5.]]])))

#LSTM 레이어
# 곱셈 문제 데이터 생성 
X = []
Y = []
for i in range(3000):
    lst = np.random.rand(100) # 0 ~ 1 사이의 랜덤 숫자 100개 생성
    idx = np.random.choice(100, 2, replace=False) #2개를 선택.
    zeros = np.zeros(100) 
    zeros[idx] = 1 #선택된 2개의 인덱스의 값을 1로 설정. 
    X.append(np.array(list(zip(zeros, lst))))
    # X 중 값이 1인 것만 lst값을 곱해서 Y 데이터에 저장함
    Y.append(np.prod(lst[idx]))
print(X[0], Y[0])

#SimpleRNN 레이어를 사용한 곱셈 문제 모델 정의
model = tf.keras.Sequential([
    tf.keras.layers.SimpleRNN(units=30, return_sequences=True, input_shape=[100,2]),
    tf.keras.layers.SimpleRNN(units=30),
    tf.keras.layers.Dense(1)
])
model.compile(optimizer='adam', loss='mse')
model.summary()
X = np.array(X)
Y = np.array(Y)
history = model.fit(X[:2560], Y[:2560], epochs=100, validation_split=0.2,verbose=0)
import matplotlib.pyplot as plt
plt.plot(history.history['loss'], 'b-', label='loss')
plt.plot(history.history['val_loss'], 'r--', label='val_loss')
plt.xlabel('Epoch')
plt.legend()
plt.show()

#Test 데이터에 대한 예측 정확도 확인
model.evaluate(X[2560:], Y[2560:])
prediction = model.predict(X[2560:2560+5])
#5개 테스트 데이터에 대한 예측을 표시
for i in range(5):
    print(Y[2560+i], '\t', prediction[i][0], \
          '\tdiff:', abs(prediction[i][0] - Y[2560+i]))

# 실제 데이터와 예측 데이터의 오차가 0.04 초과이면 오답으로 결정.=>정확도 
# 440건의 데이터를 예측하기
prediction = model.predict(X[2560:])
fail = 0
for i in range(len(prediction)) :
    # 절대값(예측값 - 실제값)
    if abs(prediction[i][0] - Y[2560+i]) > 0.04 :
        fail += 1
#(440-fail) : 정답건수    
print("정확도:",(440-fail)/440 * 100,"%")    

#LSTM 레이어를 사용한 곱셈 문제 모델 정의
model = tf.keras.Sequential([
    tf.keras.layers.LSTM(units=30, return_sequences=True, input_shape=[100,2]),
    tf.keras.layers.LSTM(units=30),
    tf.keras.layers.Dense(1)
])
model.compile(optimizer='adam', loss='mse')
model.summary()
history = model.fit(X[:2560], Y[:2560], epochs=100, validation_split=0.2)

import matplotlib.pyplot as plt
plt.plot(history.history['loss'], 'b-', label='loss')
plt.plot(history.history['val_loss'], 'r--', label='val_loss')
plt.xlabel('Epoch')
plt.legend()
plt.show()

# LSTM 모델로 학습한 Test 데이터에 대한 예측 정확도 확인
model.evaluate(X[2560:], Y[2560:]) #0.0006563540664501488
prediction = model.predict(X[2560:2560+5])
for i in range(5):
    print(Y[2560+i], '\t', prediction[i][0], '\tdiff:', abs(prediction[i][0] - Y[2560+i]))

# 오차가 0.4 초과인 경우 오답으로 결정.
prediction = model.predict(X[2560:])
fail = 0
for i in range(len(prediction)) :
    if abs(prediction[i][0] - Y[2560+i]) > 0.4 :
           fail += 1
print("정확도:",(440-fail)/440 * 100,"%") #정확도: 80.68181818181817 %

#GRU 레이어 
model = tf.keras.Sequential([
    tf.keras.layers.GRU(units=30, return_sequences=True, input_shape=[100,2]),
    tf.keras.layers.GRU(units=30),
    tf.keras.layers.Dense(1)
])
model.compile(optimizer='adam', loss='mse')
model.summary()
history = model.fit(X[:2560], Y[:2560], epochs=100, validation_split=0.2)

import matplotlib.pyplot as plt
plt.plot(history.history['loss'], 'b-', label='loss')
plt.plot(history.history['val_loss'], 'r--', label='val_loss')
plt.xlabel('Epoch')
plt.legend()
plt.show()

model.evaluate(X[2560:], Y[2560:])
prediction = model.predict(X[2560:2560+5])
for i in range(5):
    print(Y[2560+i], '\t', prediction[i][0], '\tdiff:', abs(prediction[i][0] - Y[2560+i]))
    
prediction = model.predict(X[2560:])
cnt = 0
for i in range(len(prediction)):
    if abs(prediction[i][0] - Y[2560+i]) > 0.04:
        cnt += 1
print('정확도:', (440 - cnt) / 440 * 100, '%') #98.18181818181819 %