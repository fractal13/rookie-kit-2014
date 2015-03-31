SRC_FILES := \
	./client_pygame/config.py \
	./client_pygame/main.py \
	./common/game_message.pyc \
	./common/wall.pyc \
	./common/__init__.pyc \
	./common/missile.pyc \
	./common/npc.pyc \
	./common/command_message.pyc \
	./common/event_message.pyc \
	./common/event.pyc \
	./common/object.pyc \
	./common/player.pyc \
	./common/object_message.pyc \
	./common/game_comm.pyc \
	./common/game.pyc \
	./engine_client/__init__.pyc \
	./engine_client/game_engine.pyc \
	./client_pygame/pygame_client.pyc \
	./client_pygame/display/__init__.pyc \
	./client_pygame/display/display.pyc \
	./client_pygame/control/__init__.pyc \
	./client_pygame/control/control.pyc \
	./client_pygame/config.pyc \
	./engine_server/__init__.pyc \
	./engine_server/config.pyc \
	./client/__init__.pyc \
	./client/client_game_socket.pyc \
	./client/control.pyc \
	./client/display.pyc \
	./client/pygame_game.pyc \
	./client/pygame_socket_game.pyc

STARTER_SRCS := \
./client/base_control.py \
./client/pygame_game.py \
./client/client_game_socket.py \
./client/__init__.py \
./client/base_display.py \
./client/pygame_socket_game.py \
./client_pygame/config.py \
./client_pygame/main.py \
./client_pygame/pygame_client.py \
./client_pygame/control/control.py \
./client_pygame/control/__init__.py \
./client_pygame/display/display.py \
./client_pygame/display/__init__.py \
./common/game.py \
./common/game_comm.py \
./common/event.py \
./common/wall.py \
./common/game_message.py \
./common/command_message.py \
./common/object_message.py \
./common/npc.py \
./common/__init__.py \
./common/object.py \
./common/event_message.py \
./common/player.py \
./common/missile.py \
./engine_server/config.py \
./engine_server/__init__.py \
./engine_client/game_engine.py \
./engine_client/__init__.py

all: rookie-kit-2014.zip

rookie-kit-2014.zip : $(STARTER_SRCS) Makefile
	-rm -rf rookie-kit-2014
	-mkdir rookie-kit-2014
	tar -cf - $(STARTER_SRCS) | tar -xf - -C rookie-kit-2014
	zip -r $@ rookie-kit-2014
	rm -rf rookie-kit-2014

