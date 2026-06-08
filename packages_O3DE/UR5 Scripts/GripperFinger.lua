local GripperFinger = 
{
	Properties = 
	{
		GripperController = EntityId(),
		FingerId = 0,
		RaycastDir = 1,
		GripperEnterScriptEvents = ScriptEventsAssetRef(),
		GripperExitScriptEvents = ScriptEventsAssetRef(),
	}
}

function GripperFinger:OnActivate()
	self.tickHandler = TickBus.Connect(self)
	self.rigidBodyHandler = RigidBodyNotificationBus.Connect(self, self.entityId);
	
	--GripperFinger:OnTriggerEnter(self, self.entityId);
	--GripperFinger:OnTriggerExit(self, self.entityId);

	--Debug.Log(tostring(ComponentApplicationBus.Broadcast.GetEntityName(self.entityId)).." trigger handlers enabled");
end

function GripperFinger:OnDeactivate()
	if (self.tickHandler ~= nil) then
		self.tickHandler:Disconnect();
		self.tickHandler = nil;
	end

	if (self.rigidBodyHandler ~= nil) then 
		self.rigidBodyHandler:Disconnect();
		self.rigidBodyHandler = nil;
	end
	
	-- Trigger handlers
	if (self.triggerHandlerExit ~= nil) then 
		self.triggerHandlerExit:Disconnect();
		self.triggerEventExit = nil;
	end

	if (self.triggerHandlerEnter ~= nil) then 
		self.triggerHandlerEnter:Disconnect();
		self.triggerEventEnter = nil;
	end
end

function GripperFinger:OnTick(deltaTime, timePoint)

end

function GripperFinger:OnPhysicsEnabled(entityId)
	--GripperFinger:OnTriggerEnter(self, self.entityId);
	--GripperFinger:OnTriggerExit(self, self.entityId);

	--Debug.Log(tostring(ComponentApplicationBus.Broadcast.GetEntityName(self.entityId)).." trigger handlers enabled");
end

function GripperFinger:OnTriggerEnter(selfId, triggerSourceId)
	selfId.triggerEventEnter = SimulatedBody.GetOnTriggerEnterEvent(triggerSourceId);
	if selfId.triggerEventEnter ~= nil then
		selfId.triggerHandlerEnter = selfId.triggerEventEnter:Connect(
		function(tuple, event) 
			Debug.Log("Detected object enter on finger "..tostring(self.Properties.FingerId)..", sending to controller");
			otherEntityId = TriggerEvent.GetOtherEntityId(event);
			GripperFingerEnter.Event.OnGripperFingerEnter(self.Properties.GripperController, self.Properties.FingerId, otherEntityId);
		end);
		Debug.Log("Registered enter | "..tostring(ComponentApplicationBus.Broadcast.GetEntityName(triggerSourceId)));
	end
end

function GripperFinger:OnTriggerExit(selfId, triggerSourceId)
	selfId.triggerEventExit = SimulatedBody.GetOnTriggerExitEvent(triggerSourceId);
	if selfId.triggerEventExit ~= nil then
		selfId.triggerHandlerExit = selfId.triggerEventExit:Connect(
		function(tuple, event) 
			Debug.Log("Detected object exit on finger "..tostring(self.Properties.FingerId)..", sending to controller");
			GripperFingerExit.Event.OnGripperFingerExit(self.Properties.GripperController, self.Properties.FingerId); 
		end);
		Debug.Log("Registered exit | "..tostring(ComponentApplicationBus.Broadcast.GetEntityName(triggerSourceId)));
	end
end

return GripperFinger