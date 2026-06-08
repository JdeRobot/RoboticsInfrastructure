local JointMimic =
{
	Properties =
	{
		Joint = {
			default = EntityId()
		},
		InvertSign = false,
		OnlyPosition = false
	}
}

function JointMimic:OnActivate()
	self.tickHandler = TickBus.Connect(self)
	self.transformOffset = TransformBus.Event.GetLocalTranslation(self.entityId)
	
	self.oldJointRotation = Vector3.CreateZero();
end

function JointMimic:OnDeactivate()
	self.tickHandler:Disconnect()
	self.tickHandler = nil
end

function JointMimic:OnTick(deltaTime, timePoint)
	local jointRotation = TransformBus.Event.GetLocalRotation(self.Properties.Joint)
	
	-- Prevent update when not needed (helps physics to behave)
	if jointRotation == self.oldJointRotation then return
	end
	
	-- Reset local transform to move alongside the parent entity
	TransformBus.Event.SetLocalTranslation(self.entityId, self.transformOffset)
	
	if not self.Properties.OnlyPosition then
		-- Fetch rotations
		local selfRotation = TransformBus.Event.GetLocalRotation(self.entityId)
	
		local finalRotation = selfRotation
		finalRotation.z = jointRotation.z
	
		-- Invert rotation if needed
		if self.Properties.InvertSign == true then
			finalRotation.z = -finalRotation.z
		end
	
		TransformBus.Event.SetLocalRotation(self.entityId, finalRotation)
		oldJointRotation = jointRotation;
	else
		local zero = Vector3.CreateZero()
		TransformBus.Event.SetLocalRotation(self.entityId, zero)
	end
end

return JointMimic
