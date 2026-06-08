local Gripper =
{
	Properties =
	{
		ParentEntity = EntityId(),
		GripperEnterScriptEvents = ScriptEventsAssetRef(),
		GripperExitScriptEvents = ScriptEventsAssetRef(),
	}
}

function Gripper:OnActivate()
	self.tickHandler = TickBus.Connect(self)
	self.triggerEnterHandler = GripperFingerEnter.Connect(self, self.entityId);
	self.triggerExitHandler = GripperFingerExit.Connect(self, self.entityId);
	
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

	if (self.triggerEnterHandler ~= nil) then 
		self.triggerEnterHandler:Disconnect();
		self.triggerEnterHandler = nil;
	end
	
	if (self.triggerExitHandler ~= nil) then 
		self.triggerExitHandler:Disconnect();
		self.triggerExitHandler = nil;
	end
end

function Gripper:OnTick(deltaTime, framePoint)
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
-- Trigger functions
-- //////////////////////////////////////

function Gripper:OnGripperFingerEnter(fingerId, other)
	Debug.Log("Detected on "..tostring(fingerId)..": "..tostring(ComponentApplicationBus.Broadcast.GetEntityName(otherEntityId)));
	if tostring(ComponentApplicationBus.Broadcast.GetEntityName(other)) == "Box" then
		
		if fingerId == 0 then
			self.otherLeft = otherEntityId;
		elseif fingerId == 1 then
			self.otherRight = otherEntityId;
		end
		
		self.otherLeft = otherEntityId;
		Debug.Log("Box entered "..tostring(fingerId).." trigger");
		Gripper:CheckAttach();
	end
end

function Gripper:OnGripperFingerExit(fingerId, other)
	if tostring(ComponentApplicationBus.Broadcast.GetEntityName(other)) == "Box" then
		
		if fingerId == 0 then
			self.otherLeft = nil;
		elseif fingerId == 1 then
			self.otherRight = nil;
		end
		
		Debug.Log("Box exited "..tostring(fingerId).." trigger");
		Gripper:CheckAttach();
	end
end

return Gripper
