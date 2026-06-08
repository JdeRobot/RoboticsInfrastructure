local Gripper =
{
	Properties =
	{
		LeftGripper = EntityId(),
		RightGripper = EntityId(),
		ParentEntity = EntityId()
	}
}

function Gripper:OnActivate()
	self.tickHandler = TickBus.Connect(self)
	self.rigidBodyHandler = RigidBodyNotificationBus.Connect(self, self.Properties.RightGripper);
	
	self.otherLeft = nil;
	self.otherRight = nil;
	self.attachedObj = nil;
	self.attachedOgParent = nil;
	self.attachedObjOffset = nil;
end

function Gripper:OnDeactivate()
	-- Gripper handlers
	if (self.tickBusHandler ~= nil) then 
		self.tickHandler:Disconnect()
		self.tickHandler = nil
	end
	
	if (self.rigidBodyHandler ~= nil) then 
		self.rigidBodyHandler:Disconnect();
		self.rigidBodyHandler = nil;
	end

	-- Left finger handlers
	if (self.leftTriggerHandlerExit ~= nil) then 
		self.leftTriggerHandlerExit:Disconnect();
		self.leftTriggerEventExit = nil;
	end

	if (self.leftTriggerHandlerEnter ~= nil) then 
		self.leftTriggerHandlerEnter:Disconnect();
		self.leftTriggerEventEnter = nil;
	end

	-- Right finger handlers
	if (self.rightTriggerHandlerExit ~= nil) then 
		self.rightTriggerHandlerExit:Disconnect();
		self.rightTriggerEventExit = nil;
	end

	if (self.rightTriggerHandlerEnter ~= nil) then 
		self.rightTriggerHandlerEnter:Disconnect();
		self.rightTriggerEventEnter = nil;
	end
end

function Gripper:OnPhysicsEnabled(entityId)
	-- Left trigger handlers
	Gripper:LeftTriggerEnter(self, self.Properties.LeftGripper);
	Gripper:LeftTriggerExit(self, self.Properties.LeftGripper);
	
	-- Right trigger handlers
	Gripper:RightTriggerEnter(self, self.Properties.RightGripper);
	Gripper:RightTriggerExit(self, self.Properties.RightGripper);

	Debug.Log("Gripper trigger handlers enabled");
end

function Gripper:OnTick(deltaTime, framePoint)
	assert(self.leftTriggerHandlerEnter ~= nil, "Left Trigger Enter has disconnected");

	if self.attachedObj ~= nil then
		TransformBus.Event.SetLocalTranslation(self.attachedObj, self.attachedObjOffset);
	end
end

function Gripper:CheckAttach()
	if self.otherLeft == self.otherRight and self.attachedObj == nil and self.otherLeft ~= nil then
		self.attachedObj = self.otherLeft;
		self.attachedOgParent = TransformBus.Event.GetParentId(self.attachedObj);
		Debug.Log("Attaching to " ..tostring(ComponentApplicationBus.Broadcast.GetEntityName(self.attachedObj)));
		TransformBus.Event.SetParent(self.attachedObj, self.Properties.ParentEntity);
		RigidBodyRequestBus.Event.SetGravityEnabled(self.attachedObj, false);
		self.attachedObjOffset = TransformBus.Event.GetLocalTranslation(self.attachedObj);
		
	elseif (self.otherLeft ~= self.otherRight or self.otherLeft == nil or self.otherRight == nil) and self.attachedObj ~= nil then
		TransformBus.Event.SetParent(self.attachedObj, self.attachedOgParent);
		RigidBodyRequestBus.Event.SetGravityEnabled(self.attachedObj, true);
		Debug.Log("Dettaching from " ..tostring(ComponentApplicationBus.Broadcast.GetEntityName(self.attachedObj)));
		self.attachedObj = nil;
		self.attachedOgParent = nil;
		self.attachedObjOffset = nil;
	end
end

-- //////////////////////////////////////
-- Left trigger functions
-- //////////////////////////////////////
function Gripper:LeftTriggerEnter(selfId, triggerSourceId)
	selfId.leftTriggerEventEnter = SimulatedBody.GetOnTriggerEnterEvent(triggerSourceId);
	if selfId.leftTriggerEventEnter ~= nil then
		selfId.leftTriggerHandlerEnter = selfId.leftTriggerEventEnter:Connect(function(tuple, event) Gripper:LeftTriggerEnterProcess(tuple, event) end);
		Debug.Log("Registered left enter | "..tostring(ComponentApplicationBus.Broadcast.GetEntityName(triggerSourceId)));
	end
end

function Gripper:LeftTriggerEnterProcess(tuple, event)
	otherEntityId = TriggerEvent.GetOtherEntityId(event);
	Debug.Log("Detected on left: "..tostring(ComponentApplicationBus.Broadcast.GetEntityName(otherEntityId)));
	if tostring(ComponentApplicationBus.Broadcast.GetEntityName(otherEntityId)) == "Box" then
		self.otherLeft = otherEntityId;
		Debug.Log("Box entered left trigger");
		Gripper:CheckAttach();
	end
end

function Gripper:LeftTriggerExit(selfId, triggerSourceId)
	selfId.leftTriggerEventExit = SimulatedBody.GetOnTriggerExitEvent(triggerSourceId);
	if selfId.leftTriggerEventExit ~= nil then
		selfId.leftTriggerHandlerExit = selfId.leftTriggerEventExit:Connect(function(tuple, event) Gripper:LeftTriggerExitProcess(tuple, event) end);
		Debug.Log("Registered left exit | "..tostring(ComponentApplicationBus.Broadcast.GetEntityName(triggerSourceId)));
	end
end

function Gripper:LeftTriggerExitProcess(tuple, event)
	otherEntityId = TriggerEvent.GetOtherEntityId(event);
	if tostring(ComponentApplicationBus.Broadcast.GetEntityName(otherEntityId)) == "Box" then
		self.otherLeft = nil;
		Debug.Log("Box exited left trigger");
		Gripper:CheckAttach();
	end
end

-- //////////////////////////////////////
-- Right trigger functions
-- //////////////////////////////////////
function Gripper:RightTriggerEnter(selfId, triggerSourceId)
	selfId.rightTriggerEventEnter = SimulatedBody.GetOnTriggerEnterEvent(triggerSourceId);
	if selfId.rightTriggerEventEnter ~= nil then
		selfId.rightTriggerHandlerEnter = selfId.rightTriggerEventEnter:Connect(function(tuple, event) Gripper:RightTriggerEnterProcess(tuple, event) end);
		Debug.Log("Registered right enter | "..tostring(ComponentApplicationBus.Broadcast.GetEntityName(triggerSourceId)));
	end
end

function Gripper:RightTriggerEnterProcess(tuple, event)
	otherEntityId = TriggerEvent.GetOtherEntityId(event);
	Debug.Log("Detected on right: "..tostring(ComponentApplicationBus.Broadcast.GetEntityName(otherEntityId)));
	if tostring(ComponentApplicationBus.Broadcast.GetEntityName(otherEntityId)) == "Box" then
		self.otherRight = otherEntityId;
		Debug.Log("Box entered right trigger");
		Gripper:CheckAttach();
	end
end

function Gripper:RightTriggerExit(selfId, triggerSourceId)
	selfId.rightTriggerEventExit = SimulatedBody.GetOnTriggerExitEvent(triggerSourceId);
	if selfId.rightTriggerEventExit ~= nil then
		selfId.rightTriggerHandlerExit = selfId.rightTriggerEventExit:Connect(function(tuple, event) Gripper:RightTriggerExitProcess(tuple, event) end);
		Debug.Log("Registered right exit | "..tostring(ComponentApplicationBus.Broadcast.GetEntityName(triggerSourceId)));
	end
end

function Gripper:RightTriggerExitProcess(tuple, event)
	otherEntityId = TriggerEvent.GetOtherEntityId(event);
	if tostring(ComponentApplicationBus.Broadcast.GetEntityName(otherEntityId)) == "Box" then
		self.otherRight = nil;
		Debug.Log("Box exited right trigger");
		Gripper:CheckAttach();
	end
end

return Gripper
