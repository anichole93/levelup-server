from django.forms import ValidationError
from django.http import HttpResponseServerError
from django.db.models import Count, Q
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
from levelupapi.models import Event, Game, Gamer
from django.contrib.auth.models import User
from rest_framework.decorators import action


class EventView(ViewSet):
    def retrieve(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
            serializer = EventSerializer(event)
            return Response(serializer.data)
        except Event.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)
        

    def list(self, request):
        gamer = Gamer.objects.get(user=request.auth.user)
        events = Event.objects.annotate(
            attendees_count=Count('attendees'),
            joined=Count('attendees', filter=Q(attendees=gamer))
            )
        game = request.query_params.get('game', None)
        if game is not None:
            events = events.filter(game_id=game)
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        organizer = Gamer.objects.get(user=request.auth.user)
        try:
            serializer = CreateEventSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(organizer=organizer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_400_BAD_REQUEST)
        
    def update(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
            serializer = CreateEventSerializer(event, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        except ValidationError as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request, pk):
        event = Event.objects.get(pk=pk)
        event.delete()
        return Response(None, status=status.HTTP_204_NO_CONTENT)
    
    @action(methods=['post'], detail=True)
    def signup(self, request, pk):
        gamer = Gamer.objects.get(user=request.auth.user)
        event = Event.objects.get(pk=pk)
        event.attendees.add(gamer)
        return Response({'message': 'Gamer added'}, status=status.HTTP_201_CREATED)
    
    @action(methods=['delete'], detail=True)
    def leave(self, request, pk):
        gamer = Gamer.objects.get(user=request.auth.user)
        event = Event.objects.get(pk=pk)
        event.attendees.remove(gamer)
        return Response({'message': 'Gamer removed'}, status=status.HTTP_204_NO_CONTENT)
    


class EventSerializer(serializers.ModelSerializer):
    attendees_count = serializers.IntegerField(default=None)
    class Meta:
        model = Event
        fields = ('id', 'description', 'date', 'time', 'game', 'organizer', 'attendees', 'joined', 'attendees_count')
        depth = 2
        
class CreateEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['description', 'date', 'time', 'game']